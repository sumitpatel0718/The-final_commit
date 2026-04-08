// ============================
// Fitter.h
// ============================

#ifndef FITTER_H
#define FITTER_H

#include <QVector>
#include <QPointF>

class Fitter
{
public:
    Fitter();

    QVector<QPointF> getLineData();
    QVector<QPointF> getScatterData();
};

#endif


// ============================
// Fitter.cpp
// ============================

#include "Fitter.h"

Fitter::Fitter()
{
}

QVector<QPointF> Fitter::getLineData()
{
    QVector<QPointF> data;

    data.append(QPointF(0,1));
    data.append(QPointF(1,5));
    data.append(QPointF(2,3));

    return data;
}

QVector<QPointF> Fitter::getScatterData()
{
    QVector<QPointF> data;

    data.append(QPointF(0,1));
    data.append(QPointF(1,5));
    data.append(QPointF(2,3));

    return data;
}


// ============================
// MainWindow.h
// ============================

#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QtCharts/QChart>
#include <QtCharts/QChartView>
#include <QtCharts/QLineSeries>
#include <QtCharts/QScatterSeries>
#include <QtCharts/QValueAxis>

#include "Fitter.h"

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

QT_CHARTS_USE_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

    void onDataAvailable(QString us_dtr);

private slots:
    void on_refreshButton_clicked();

private:
    void updateChart();

private:
    Ui::MainWindow *ui;

    QChart* chart;
    QChartView* chartView;

    QLineSeries* lineSeries;
    QScatterSeries* scatterSeries;

    QValueAxis* axisX;
    QValueAxis* axisY;
};

#endif


// ============================
// MainWindow.cpp
// ============================

#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QMetaObject>
#include <algorithm>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    // Chart
    chart = new QChart();
    chartView = new QChartView(chart);

    ui->verticalLayout->addWidget(chartView);

    // Series
    lineSeries = new QLineSeries();
    scatterSeries = new QScatterSeries();

    chart->addSeries(lineSeries);
    chart->addSeries(scatterSeries);

    // Axis
    axisX = new QValueAxis();
    axisY = new QValueAxis();

    axisX->setRange(0,1);
    axisY->setRange(0,1);

    chart->addAxis(axisX, Qt::AlignBottom);
    chart->addAxis(axisY, Qt::AlignLeft);

    lineSeries->attachAxis(axisX);
    lineSeries->attachAxis(axisY);

    scatterSeries->attachAxis(axisX);
    scatterSeries->attachAxis(axisY);
}

MainWindow::~MainWindow()
{
    delete ui;
}


// ============================
// Common Chart Update
// ============================

void MainWindow::updateChart()
{
    Fitter fitter;

    const auto lineData = fitter.getLineData();
    const auto scatterData = fitter.getScatterData();

    if (lineData.isEmpty())
        return;

    lineSeries->replace(lineData);
    scatterSeries->replace(scatterData);

    double minX = lineData.first().x();
    double maxX = minX;
    double minY = lineData.first().y();
    double maxY = minY;

    for (const auto& p : lineData)
    {
        minX = std::min(minX, p.x());
        maxX = std::max(maxX, p.x());

        minY = std::min(minY, p.y());
        maxY = std::max(maxY, p.y());
    }

    axisX->setRange(minX, maxX);
    axisY->setRange(minY, maxY);
}


// ============================
// RTI Data Available
// ============================

void MainWindow::onDataAvailable(QString us_dtr)
{
    QMetaObject::invokeMethod(
        this,
        &MainWindow::updateChart,
        Qt::QueuedConnection
    );
}


// ============================
// Refresh Button
// ============================

void MainWindow::on_refreshButton_clicked()
{
    updateChart();
}
