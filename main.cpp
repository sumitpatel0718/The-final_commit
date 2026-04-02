#include <iostream>
#include <vector>
#include <cmath>
#include <random>
#include <algorithm>
#include <Eigen/Dense>
#include <unsupported/Eigen/NonLinearOptimization>
#include <unsupported/Eigen/NumericalDiff>

using namespace std;

// =====================================================================
// STANDARD EIGEN FUNCTOR BASE
// =====================================================================
template<typename _Scalar, int NX = Eigen::Dynamic, int NY = Eigen::Dynamic>
struct Functor {
    typedef _Scalar Scalar;
    enum { InputsAtCompileTime = NX, ValuesAtCompileTime = NY };
    typedef Eigen::Matrix<Scalar, InputsAtCompileTime, 1> InputType;
    typedef Eigen::Matrix<Scalar, ValuesAtCompileTime, 1> ValueType;
    typedef Eigen::Matrix<Scalar, ValuesAtCompileTime, InputsAtCompileTime> JacobianType;

    int m_inputs, m_values;
    Functor(int inputs, int values) : m_inputs(inputs), m_values(values) {}
    int inputs() const { return m_inputs; }
    int values() const { return m_values; }
};


// =====================================================================
// def svi_total_variance(params, k):
// =====================================================================
vector<double> svi_total_variance(const vector<double>& params, const vector<double>& k_array) {
    double a = params[0], b = params[1], rho = params[2], m = params[3], sigma = params[4];
    vector<double> res(k_array.size());
    
    for (size_t i = 0; i < k_array.size(); ++i) {
        double k = k_array[i];
        res[i] = a + b * (rho * (k - m) + sqrt(pow(k - m, 2) + pow(sigma, 2)));
    }
    return res;
}


// =====================================================================
// def objective(p): 
// FIX: We use <double, Eigen::Dynamic, Eigen::Dynamic> here to ensure 
// the internal Jacobian is fully dynamic (Eigen::MatrixXd).
// This completely solves the lvalue reference compile error.
// =====================================================================
struct objective : Functor<double, Eigen::Dynamic, Eigen::Dynamic> {
    const vector<double>& k;
    const vector<double>& total_var;

    objective(const vector<double>& k_, const vector<double>& tv_) 
        : Functor<double, Eigen::Dynamic, Eigen::Dynamic>(5, k_.size()), k(k_), total_var(tv_) {}

    int operator()(const Eigen::VectorXd& p, Eigen::VectorXd& fvec) const {
        vector<double> params = {p[0], p[1], p[2], p[3], p[4]};
        vector<double> model = svi_total_variance(params, k);

        double lb[5] = {1e-8, 1e-8, -0.999, -1.0, 1e-6};
        double ub[5] = {5.0,  5.0,   0.999,  1.0, 5.0};

        for (size_t i = 0; i < k.size(); ++i) {
            fvec[i] = model[i] - total_var[i]; 
            
            // Soft-bounds
            for (int j = 0; j < 5; ++j) {
                if (p[j] < lb[j]) fvec[i] += 10000.0 * (lb[j] - p[j]);
                if (p[j] > ub[j]) fvec[i] += 10000.0 * (p[j] - ub[j]);
            }
        }
        return 0;
    }
};


// =====================================================================
// def fit_svi(k, total_var):
// =====================================================================
vector<double> fit_svi(const vector<double>& k, const vector<double>& total_var) {
    Eigen::VectorXd x0(5);
    x0 << 0.01, 0.1, -0.3, 0.0, 0.1;

    objective obj(k, total_var);
    Eigen::NumericalDiff<objective> numDiff(obj);
    Eigen::LevenbergMarquardt<Eigen::NumericalDiff<objective>> lm(numDiff);
    
    lm.minimize(x0); 

    // Clamp strictly to bounds before returning
    double lb[5] = {1e-8, 1e-8, -0.999, -1.0, 1e-6};
    double ub[5] = {5.0,  5.0,   0.999,  1.0, 5.0};
    vector<double> final_params(5);
    for (int i = 0; i < 5; ++i) {
        final_params[i] = max(lb[i], min(x0[i], ub[i]));
    }

    return final_params;
}


// =====================================================================
// MAIN SCRIPT
// =====================================================================
int main() {
    mt19937 gen(42); 
    uniform_real_distribution<> uniform_dist(-0.5, 0.5);
    normal_distribution<> normal_dist(0, 0.005);

    // k_data = np.random.uniform(-0.5, 0.5, 75)
    vector<double> k_data(75);
    for (int i = 0; i < 75; ++i) k_data[i] = uniform_dist(gen);
    
    // k_data.sort()
    sort(k_data.begin(), k_data.end());

    // true_params = [0.04, 0.2, -0.4, 0.1, 0.1]
    vector<double> true_params = {0.04, 0.2, -0.4, 0.1, 0.1};

    // tv_data = svi_total_variance(true_params, k_data) + np.random.normal(0, 0.005, 75)
    vector<double> tv_data = svi_total_variance(true_params, k_data);
    for (int i = 0; i < 75; ++i) tv_data[i] += normal_dist(gen);

    // -------------------------------------------------------------
    // py_params = fit_svi(k_data, tv_data)
    vector<double> py_params = fit_svi(k_data, tv_data);

    // py_fit = svi_total_variance(py_params, k_data)
    vector<double> py_fit = svi_total_variance(py_params, k_data);
    // -------------------------------------------------------------

    // Print Results
    cout << "--- Output Parameters ---" << endl;
    cout << "a     = " << py_params[0] << endl;
    cout << "b     = " << py_params[1] << endl;
    cout << "rho   = " << py_params[2] << endl;
    cout << "m     = " << py_params[3] << endl;
    cout << "sigma = " << py_params[4] << endl;

    return 0;
}

/*

how to run ->g++ main.cpp -o main.exe -I C:\Users\sumit\Downloads\eigen-3.4.0\eigen-3.4.0 -O3
.\main.exe
