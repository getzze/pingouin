import pytest
import numpy as np
from unittest import TestCase
from pingouin.parametric import (ttest, anova, rm_anova, mixed_anova,
                                 ancova, welch_anova)
from pingouin import read_dataset

# Generate random data for ANOVA
df = read_dataset('mixed_anova.csv')

df_nan = df.copy()
df_nan.iloc[[4, 15], 0] = np.nan

# Create random normal variables
np.random.seed(1234)
x = np.random.normal(scale=1., size=100)
y = np.random.normal(scale=0.8, size=100)


class TestParametric(TestCase):
    """Test parametric.py."""

    def test_ttest(self):
        """Test function ttest"""
        h = np.random.normal(scale=0.9, size=95)
        ttest(x, 0.5)
        stats = ttest(x, y, paired=True, tail='one-sided')
        # Compare with JASP
        assert np.allclose(stats.loc['T-test', 'T'], 0.616)
        assert np.allclose(stats.loc['T-test', 'p-val'].round(3), .270)
        ttest(x, y, paired=False, correction='auto')
        ttest(x, y, paired=False, correction=True)
        ttest(x, y, paired=False, r=0.5)
        ttest(x, h, paired=True)
        # Compare with R t.test
        a = [4, 7, 8, 6, 3, 2]
        b = [6, 8, 7, 10, 11, 9]
        tt = ttest(a, b, paired=False, correction=False, tail='two-sided')
        assert tt.loc['T-test', 'T'] == -2.842
        assert tt.loc['T-test', 'dof'] == 10
        assert round(tt.loc['T-test', 'p-val'], 5) == 0.01749
        np.testing.assert_allclose(tt.loc['T-test', 'CI95%'], [-6.24, -0.76])
        # - Two sample unequal variances
        tt = ttest(a, b, paired=False, correction=True, tail='two-sided')
        assert tt.loc['T-test', 'dof'] == 9.49
        assert round(tt.loc['T-test', 'p-val'], 5) == 0.01837
        np.testing.assert_allclose(tt.loc['T-test', 'CI95%'], [-6.26, -0.74])
        # - Paired
        tt = ttest(a, b, paired=True, correction=False, tail='two-sided')
        assert tt.loc['T-test', 'T'] == -2.445
        assert tt.loc['T-test', 'dof'] == 5
        assert round(tt.loc['T-test', 'p-val'], 5) == 0.05833
        np.testing.assert_allclose(tt.loc['T-test', 'CI95%'], [-7.18, 0.18])
        # - One sample one-sided
        tt = ttest(a, y=0, paired=False, correction=False, tail='one-sided')
        assert tt.loc['T-test', 'T'] == 5.175
        assert tt.loc['T-test', 'dof'] == 5
        assert round(tt.loc['T-test', 'p-val'], 3) == 0.002
        np.testing.assert_allclose(tt.loc['T-test', 'CI95%'], [3.05, np.inf])
        # - Two-sample equal variances, tail = 'greater'
        tt = ttest(a, b, paired=False, tail='greater')
        assert tt.loc['T-test', 'tail'] == 'greater'
        assert round(tt.loc['T-test', 'p-val'], 4) == 0.9913
        assert float(tt.loc['T-test', 'BF10']) < 1
        np.testing.assert_allclose(tt.loc['T-test', 'CI95%'], [-5.73, np.inf])
        # tail = 'less'
        tt = ttest(a, b, paired=False, tail='less')
        assert tt.loc['T-test', 'tail'] == 'less'
        assert round(tt.loc['T-test', 'p-val'], 5) == 0.00874
        assert float(tt.loc['T-test', 'BF10']) > 1
        np.testing.assert_allclose(tt.loc['T-test', 'CI95%'], [-np.inf, -1.27])

    def test_anova(self):
        """Test function anova.
        Compare results to JASP.
        """
        # Pain dataset
        df_pain = read_dataset('anova')
        aov = anova(dv='Pain threshold', between='Hair color', data=df_pain,
                    detailed=True, export_filename='test_export.csv')
        anova(dv='Pain threshold', between=['Hair color'], data=df_pain)
        # Compare with JASP
        assert np.allclose(aov.loc[0, 'F'], 6.791)
        assert np.allclose(np.round(aov.loc[0, 'p-unc'], 3), .004)
        assert np.allclose(aov.loc[0, 'np2'], .576)
        # Unbalanced and with missing values
        df_pain.loc[[17, 18], 'Pain threshold'] = np.nan
        aov = df_pain.anova(dv='Pain threshold', between='Hair color').round(3)
        assert aov.loc[0, 'ddof1'] == 3
        assert aov.loc[0, 'ddof2'] == 13
        assert aov.loc[0, 'F'] == 4.359
        assert aov.loc[0, 'p-unc'] == 0.025
        assert aov.loc[0, 'np2'] == 0.501
        # Error: between is an empty list
        with pytest.raises(ValueError):
            anova(dv='Pain threshold', between=[], data=df_pain)
        # Two-way ANOVA with balanced design
        df_aov2 = read_dataset('anova2')
        aov2 = anova(dv="Yield", between=["Blend", "Crop"],
                     data=df_aov2).round(3)
        assert aov2.loc[0, 'MS'] == 2.042
        assert aov2.loc[1, 'MS'] == 1368.292
        assert aov2.loc[2, 'MS'] == 1180.042
        assert aov2.loc[3, 'MS'] == 541.847
        assert aov2.loc[0, 'F'] == 0.004
        assert aov2.loc[1, 'F'] == 2.525
        assert aov2.loc[2, 'F'] == 2.178
        assert aov2.loc[0, 'p-unc'] == 0.952
        assert aov2.loc[1, 'p-unc'] == 0.108
        assert aov2.loc[2, 'p-unc'] == 0.142
        assert aov2.loc[0, 'np2'] == 0.000
        assert aov2.loc[1, 'np2'] == 0.219
        assert aov2.loc[2, 'np2'] == 0.195
        # Export
        anova(dv="Yield", between=["Blend", "Crop"],
              export_filename='test_export.csv', data=df_aov2)
        # Two-way ANOVA with unbalanced design
        df_aov2 = read_dataset('anova2_unbalanced')
        aov2 = df_aov2.anova(dv="Scores", export_filename='test_export.csv',
                             between=["Diet", "Exercise"]).round(3)
        assert aov2.loc[0, 'MS'] == 390.625
        assert aov2.loc[1, 'MS'] == 180.625
        assert aov2.loc[2, 'MS'] == 15.625
        assert aov2.loc[3, 'MS'] == 52.625
        assert aov2.loc[0, 'F'] == 7.423
        assert aov2.loc[1, 'F'] == 3.432
        assert aov2.loc[2, 'F'] == 0.297
        assert aov2.loc[0, 'p-unc'] == 0.034
        assert aov2.loc[1, 'p-unc'] == 0.113
        assert aov2.loc[2, 'p-unc'] == 0.605
        assert aov2.loc[0, 'np2'] == 0.553
        assert aov2.loc[1, 'np2'] == 0.364
        assert aov2.loc[2, 'np2'] == 0.047
        # Two-way ANOVA with unbalanced design and missing values
        df_aov2.loc[9, 'Scores'] = np.nan
        # Type 2
        aov2 = anova(dv="Scores", between=["Diet", "Exercise"],
                     data=df_aov2).round(3)
        assert aov2.loc[0, 'F'] == 10.403
        assert aov2.loc[1, 'F'] == 5.167
        assert aov2.loc[2, 'F'] == 0.761
        assert aov2.loc[0, 'p-unc'] == 0.023
        assert aov2.loc[1, 'p-unc'] == 0.072
        assert aov2.loc[2, 'p-unc'] == 0.423
        assert aov2.loc[0, 'np2'] == 0.675
        assert aov2.loc[1, 'np2'] == 0.508
        assert aov2.loc[2, 'np2'] == 0.132
        aov2_ss1 = anova(dv="Scores", between=["Diet", "Exercise"],
                         ss_type=1, data=df_aov2).round(3)
        assert not aov2.equals(aov2_ss1)

        # Three-way ANOVA using statsmodels
        # Balanced
        df_aov3 = read_dataset('anova3')
        aov3_ss1 = anova(dv="Cholesterol", between=['Sex', 'Risk', 'Drug'],
                         ss_type=1, data=df_aov3,
                         export_filename='test_export.csv').round(3)
        aov3_ss2 = anova(dv="Cholesterol", between=['Sex', 'Risk', 'Drug'],
                         ss_type=2, data=df_aov3).round(3)
        aov3_ss3 = anova(dv="Cholesterol", between=['Sex', 'Risk', 'Drug'],
                         ss_type=3, data=df_aov3).round(3)
        # Check that type 1 == type 2 == type 3
        assert aov3_ss1.equals(aov3_ss2)
        assert aov3_ss2.equals(aov3_ss3)
        # Compare with JASP
        np.testing.assert_array_equal(aov3_ss1.loc[:, 'F'],
                                      [2.462, 13.449, 0.484, 0.139, 1.522,
                                       1.446, 1.094, np.nan])
        np.testing.assert_array_equal(aov3_ss1.loc[:, 'np2'],
                                      [0.049, 0.219, 0.020, 0.003, 0.060,
                                       0.057, 0.044, np.nan])
        np.testing.assert_array_equal(aov3_ss1.loc[:, 'p-unc'],
                                      [0.123, 0.001, 0.619, 0.711, 0.229,
                                       0.245, 0.343, np.nan])
        # Unbalanced
        df_aov3 = read_dataset('anova3_unbalanced')
        aov3_ss1 = anova(dv="Cholesterol", between=['Sex', 'Risk', 'Drug'],
                         ss_type=1, data=df_aov3).round(3)
        aov3_ss2 = anova(dv="Cholesterol", between=['Sex', 'Risk', 'Drug'],
                         ss_type=2, data=df_aov3).round(3)
        aov3_ss3 = anova(dv="Cholesterol", between=['Sex', 'Risk', 'Drug'],
                         ss_type=3, data=df_aov3).round(3)
        # Compare with JASP
        # Type 1
        np.testing.assert_array_equal(aov3_ss1.loc[:, 'F'],
                                      [4.155, 15.166, 0.422, 0.085, 0.859,
                                       1.170, 0.505, np.nan])
        np.testing.assert_array_equal(aov3_ss1.loc[:, 'np2'],
                                      [0.068, 0.210, 0.015, 0.001, 0.029,
                                       0.039, 0.017, np.nan])
        np.testing.assert_array_equal(aov3_ss1.loc[:, 'p-unc'],
                                      [0.046, 0., 0.658, 0.772, 0.429,
                                       0.318, 0.606, np.nan])
        np.testing.assert_array_equal(aov3_ss1.loc[:, 'Source'],
                                      ['Sex', 'Risk', 'Drug', 'Sex * Risk',
                                       'Sex * Drug', 'Risk * Drug',
                                       'Sex * Risk * Drug', 'Residual'])
        # Type 2
        np.testing.assert_array_equal(aov3_ss2.loc[:, 'F'],
                                      [3.759, 15.169, 0.429, 0.099, 0.739,
                                       1.170, 0.505, np.nan])
        np.testing.assert_array_equal(aov3_ss2.loc[:, 'np2'],
                                      [0.062, 0.210, 0.015, 0.002, 0.025,
                                       0.039, 0.017, np.nan])
        np.testing.assert_array_equal(aov3_ss2.loc[:, 'p-unc'],
                                      [0.057, 0., 0.653, 0.754, 0.482,
                                       0.318, 0.606, np.nan])

        # Type 3
        np.testing.assert_array_equal(aov3_ss3.loc[:, 'F'],
                                      [3.910, 15.555, 0.484, 0.079, 0.750,
                                       1.060, 0.505, np.nan])
        np.testing.assert_array_equal(aov3_ss3.loc[:, 'np2'],
                                      [0.064, 0.214, 0.017, 0.001, 0.026,
                                       0.036, 0.017, np.nan])
        np.testing.assert_array_equal(aov3_ss3.loc[:, 'p-unc'],
                                      [0.053, 0., 0.619, 0.779, 0.477,
                                       0.353, 0.606, np.nan])

        # Error: invalid char in column names
        df_aov3['Sex:'] = np.random.normal(size=df_aov3.shape[0])
        with pytest.raises(ValueError):
            anova(dv='Cholesterol', between=['Sex:', 'Risk', 'Drug'],
                  data=df_aov3)

    def test_welch_anova(self):
        """Test function welch_anova."""
        # Pain dataset
        df_pain = read_dataset('anova')
        aov = welch_anova(dv='Pain threshold', between='Hair color',
                          data=df_pain, export_filename='test_export.csv')
        # Compare with R oneway.test function
        assert aov.loc[0, 'ddof1'] == 3
        assert np.allclose(aov.loc[0, 'ddof2'], 8.330)
        assert np.allclose(aov.loc[0, 'F'], 5.890)
        assert np.allclose(np.round(aov.loc[0, 'p-unc'], 4), .0188)

    def test_rm_anova(self):
        """Test function rm_anova.
        Compare with JASP"""
        rm_anova(dv='Scores', within='Time', subject='Subject', data=df,
                 correction=False, detailed=False)
        rm_anova(dv='Scores', within='Time', subject='Subject', data=df,
                 correction=True, detailed=False)
        aov = rm_anova(dv='Scores', within='Time', subject='Subject', data=df,
                       correction='auto', detailed=True)
        # Compare with JASP
        assert np.allclose(aov.loc[0, 'F'], 3.913)
        assert np.allclose(np.round(aov.loc[0, 'p-unc'], 3), .023)
        assert np.allclose(aov.loc[0, 'np2'], .062)

        rm_anova(dv='Scores', within='Time', subject='Subject', data=df,
                 correction=True, detailed=True)
        rm_anova(dv='Scores', within=['Time'], subject='Subject', data=df_nan,
                 export_filename='test_export.csv')
        # Using a wide dataframe with NaN and compare with JASP
        data = read_dataset('rm_anova_wide')
        aov = data.rm_anova(detailed=True, correction=True)
        assert aov.loc[0, 'F'] == 5.201
        assert round(aov.loc[0, 'p-unc'], 3) == .007
        assert aov.loc[0, 'np2'] == .394
        assert aov.loc[0, 'eps'] == .694
        assert aov.loc[0, 'W-spher'] == .307
        assert round(aov.loc[0, 'p-GG-corr'], 3) == .017

    def test_rm_anova2(self):
        """Test function rm_anova2.
        Compare with JASP."""
        data = read_dataset('rm_anova2')
        aov = rm_anova(data=data, subject='Subject', within=['Time', 'Metric'],
                       dv='Performance',
                       export_filename='test_export.csv').round(3)
        assert aov.loc[0, "MS"] == 828.817
        assert aov.loc[1, "MS"] == 682.617
        assert aov.loc[2, "MS"] == 112.217
        assert aov.loc[0, "F"] == 33.852
        assert aov.loc[1, "F"] == 26.959
        assert aov.loc[2, "F"] == 12.632
        assert aov.loc[0, "np2"] == 0.790
        assert aov.loc[1, "np2"] == 0.750
        assert aov.loc[2, "np2"] == 0.584
        assert aov.loc[0, "eps"] == 1.000
        assert aov.loc[1, "eps"] == 0.969
        assert aov.loc[2, "eps"] >= 0.500  # 0.5 is the lower bound

        # With missing values
        df2 = read_dataset('rm_missing')
        df2.rm_anova(dv='BOLD', within=['Session', 'Time'], subject='Subj')

        # Error: more than two factors
        with pytest.raises(ValueError):
            df2.rm_anova(dv='BOLD', within=['Session', 'Time', 'Wrong'],
                         subject='Subj')

    def test_mixed_anova(self):
        """Test function anova.
        Compare with JASP and ezANOVA."""
        aov = mixed_anova(dv='Scores', within='Time', subject='Subject',
                          between='Group', data=df, correction=True).round(3)
        # Compare with ezANOVA / JASP
        assert aov.loc[0, 'SS'] == 5.460
        assert aov.loc[1, 'SS'] == 7.628
        assert aov.loc[2, 'SS'] == 5.168
        assert aov.loc[0, 'F'] == 5.052
        assert aov.loc[1, 'F'] == 4.027
        assert aov.loc[2, 'F'] == 2.728
        assert aov.loc[0, 'np2'] == 0.080
        assert aov.loc[1, 'np2'] == 0.065
        assert aov.loc[2, 'np2'] == 0.045
        assert aov.loc[1, 'eps'] == 0.999
        assert aov.loc[1, 'W-spher'] == 0.999
        assert round(aov.loc[1, 'p-GG-corr'], 2) == 0.02
        # With missing values
        df_nan2 = df_nan.copy()
        df_nan2.iloc[158, 0] = np.nan
        aov = mixed_anova(dv='Scores', within='Time', subject='Subject',
                          between='Group', data=df_nan2, correction=True,
                          export_filename='test_export.csv').round(3)
        # Compare with ezANOVA / JASP
        assert aov.loc[0, 'F'] == 5.692
        assert aov.loc[1, 'F'] == 3.053
        assert aov.loc[2, 'F'] == 3.501
        assert aov.loc[0, 'np2'] == 0.094
        assert aov.loc[1, 'np2'] == 0.053
        assert aov.loc[2, 'np2'] == 0.060
        assert aov.loc[1, 'eps'] == 0.997
        assert aov.loc[1, 'W-spher'] == 0.996
        # Unbalanced group
        df_unbalanced = df[df["Subject"] <= 54]
        aov = mixed_anova(data=df_unbalanced, dv='Scores',
                          subject='Subject', within='Time', between='Group',
                          correction=True).round(3)
        # Compare with ezANOVA / JASP
        assert aov.loc[0, 'F'] == 3.561
        assert aov.loc[1, 'F'] == 2.421
        assert aov.loc[2, 'F'] == 1.827
        assert aov.loc[0, 'np2'] == 0.063
        assert aov.loc[1, 'np2'] == 0.044
        assert aov.loc[2, 'np2'] == 0.033
        assert aov.loc[1, 'eps'] == 1.  # JASP = 0.998
        assert aov.loc[1, 'W-spher'] == 1.  # JASP = 0.998

    def test_ancova(self):
        """Test function ancovan.
        Compare with JASP."""
        df = read_dataset('ancova')
        # With one covariate, balanced design, no missing values
        aov = ancova(data=df, dv='Scores', covar='Income',
                     between='Method').round(3)
        assert aov.loc[0, 'F'] == 3.336
        assert aov.loc[1, 'F'] == 29.419
        # With one covariate, missing values and unbalanced design
        df.loc[[1, 2], 'Scores'] = np.nan
        aov = ancova(data=df, dv='Scores', covar=['Income'],
                     between='Method',
                     export_filename='test_export.csv').round(3)
        assert aov.loc[0, 'F'] == 3.147
        assert aov.loc[1, 'F'] == 19.781
        assert aov.loc[2, 'DF'] == 29
        # With two covariates, missing values and unbalanced design
        aov = ancova(data=df, dv='Scores', covar=['Income', 'BMI'],
                     between='Method')
        assert aov.loc[0, 'F'] == 3.019
        assert aov.loc[1, 'F'] == 19.605
        assert aov.loc[2, 'F'] == 1.228
        assert aov.loc[3, 'DF'] == 28
        # Other parameters
        ancova(data=df, dv='Scores', covar=['Income', 'BMI'],
               between='Method', export_filename='test_export.csv')
        ancova(data=df, dv='Scores', covar=['Income'], between='Method')
