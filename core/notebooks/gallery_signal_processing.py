# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# ## Import

# %%
# %load_ext autoreload
# %autoreload 2
# %matplotlib inline

import collections
import logging
import pprint

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import core.artificial_signal_generators as sig_gen
import core.plotting as plot
import core.signal_processing as sigp
import core.statistics as stats
import helpers.dbg as dbg
import helpers.env as env
import helpers.printing as prnt

# %%
dbg.init_logger(verbosity=logging.INFO)

_LOG = logging.getLogger(__name__)

_LOG.info("%s", env.get_system_signature()[0])

prnt.config_notebook()

# %% [markdown]
# # Generate signal

# %%
arma00process = sig_gen.ArmaProcess([], [])

# %%
rets = arma00process.generate_sample(
    {"start": "2000-01-01", "periods": 4 * 252, "freq": "B"},
    scale=0.01,
    burnin=20,
    seed=42,
)

# %%
price = np.exp(rets.cumsum())

# %%
rets.name += "_rets"
price.name += "_price"

# %% [markdown]
# ## Price

# %%
plot.plot_cols(price)

# %%
price_decomp = sigp.get_trend_residual_decomp(price, tau=16)

# %%
price_decomp.head(3)

# %%
plot.plot_cols(price_decomp)

# %%
price_decomp.apply(stats.apply_adf_test)

# %% [markdown]
# ### Price wavelet decomposition

# %%
price_smooth, price_detail = sigp.get_swt(price, wavelet="haar")

# %%
plot.plot_cols(price_detail)

# %%
plot.plot_cols(price_smooth)

# %%
plot.plot_correlation_matrix(price_detail, mode="heatmap")

# %% [markdown]
# ## Returns

# %%
plot.plot_cols(rets)

# %%
stats.apply_normality_test(rets).to_frame()

# %%
plot.plot_autocorrelation(rets)

# %%
plot.plot_spectrum(rets)

# %% [markdown]
# ### Returns wavelet decomposition

# %%
rets_smooth, rets_detail = sigp.get_swt(rets, "haar")

# %%
plot.plot_cols(rets_detail)

# %%
plot.plot_cols(rets_detail, mode="renormalize")

# %%
rets_detail.apply(stats.apply_normality_test)

# %%
plot.plot_autocorrelation(rets_detail, title_prefix="Wavelet level ")

# %%
plot.plot_spectrum(rets_detail, title_prefix="Wavelet level ")

# %%
plot.plot_correlation_matrix(rets_detail, mode="heatmap")

# %% [markdown]
# ### Z-scored returns

# %%
zscored_rets = sigp.get_dyadic_zscored(rets, demean=False)

# %%
plot.plot_cols(zscored_rets)

# %%
zscored_rets.apply(stats.apply_normality_test)

# %%
plot.plot_autocorrelation(zscored_rets, title_prefix="tau exp = ")

# %%
plot.plot_spectrum(zscored_rets, title_prefix="tau exp = ")

# %%

# %% [markdown]
# # EMAs and Smooth Moving Averages

# %%
impulse = sig_gen.get_impulse(-252, 3 * 252, tick=1)

# %%
impulse.plot()

# %% [markdown]
# ## Dependence of ema on depth

# %%
for i in range(1, 6):
    sigp.compute_ema(impulse, tau=40, min_periods=20, depth=i).plot()

# %% [markdown]
# ## Dependence of smooth moving average on max depth

# %%
for i in range(1, 6):
    sigp.compute_smooth_moving_average(
        impulse, tau=40, min_periods=20, min_depth=1, max_depth=i
    ).plot()

# %% [markdown]
# ## Dependence of smooth moving average on min depth

# %%
for i in range(1, 6):
    sigp.compute_smooth_moving_average(
        impulse, tau=40, min_periods=20, min_depth=i, max_depth=5
    ).plot()

# %% [markdown]
# ## Dependence of rolling norm on max depth

# %%
for i in range(1, 6):
    sigp.compute_rolling_norm(
        impulse, tau=40, min_periods=20, min_depth=1, max_depth=i, p_moment=1
    ).plot()

# %% [markdown]
# ## Dependence of rolling norm on moment

# %%
for i in np.arange(0.5, 4.5, 0.5):
    sigp.compute_rolling_norm(
        impulse, tau=40, min_periods=20, min_depth=1, max_depth=2, p_moment=i
    ).plot()

# %% [markdown]
# # Smooth Derivatives

# %% [markdown]
# ## Dependence on tau

# %%
for i in range(1, 6):
    sigp.compute_smooth_derivative(
        impulse, tau=100 * i, min_periods=0, scaling=0, order=1
    ).plot()

# %% [markdown]
# ## Dependence on order

# %%
for i in range(1, 6):
    sigp.compute_smooth_derivative(
        impulse, tau=100, min_periods=0, scaling=0, order=i
    ).plot()

# %% [markdown]
# ## Application to slope 1 linear growth with varying tau, scaling = 1

# %%
linear_growth = pd.Series(index=price.index, data=range(price.size))

# %%
for i in range(1, 6):
    sigp.compute_smooth_derivative(
        linear_growth, tau=2 ** i, min_periods=0, scaling=1, order=1
    ).plot()

# %% [markdown]
# ## Application to prices

# %%
dprice = pd.DataFrame(index=price.index)
dprice["rets"] = rets

# %%
for i in range(0, 7):
    dprice[i] = sigp.compute_smooth_derivative(
        price, tau=2 ** i, min_periods=0, scaling=1, order=1
    )

# %%
plot.plot_cols(dprice)

# %%
plot.plot_cols(dprice.cumsum(), mode="renormalize")

# %% [markdown]
# # Multivariate series

# %%
mvn = sig_gen.MultivariateNormalProcess()
mvn.set_cov_from_inv_wishart_draw(dim=8, seed=10)
mvn_rets = mvn.generate_sample(
    {"start": "2000-01-01", "periods": 4 * 252, "freq": "B"}, seed=10
)

# %%
plot.plot_cols(mvn_rets)

# %% [markdown]
# ## Z-score the time series

# %%
mvn_zrets = sigp.compute_rolling_zscore(mvn_rets, tau=16, demean=False)

# %%
plot.plot_cols(mvn_zrets)

# %% [markdown]
# ## Compute Incremental PCA

# %%
eigenvalues, eigenvectors = sigp.compute_ipca(mvn_zrets, num_pc=3, tau=16)

# %% [markdown]
# ### Plot eigenvalue evolution over time

# %%
plot.plot_cols(eigenvalues)

# %% [markdown]
# ### Plot eigenvector evolution over time

# %%
eigenvectors[0].plot()

# %%
eigenvectors[1].plot()

# %%
eigenvectors[2].plot()

# %% [markdown]
# ### Plot eigenvector angular distance change over time

# %%
eigenvector_diffs = sigp.compute_eigenvector_diffs(eigenvectors)

# %%
plot.plot_cols(eigenvector_diffs)

# %% [markdown]
# # Outlier handling

# %%
np.random.seed(100)
n = 100000
data = np.random.normal(loc=0.0, scale=1.0, size=n)
print(data[:5])

srs = pd.Series(data)
srs.plot(kind="hist")


# %%
def _analyze(srs):
    print(np.isnan(srs).sum())
    srs.plot(kind="hist")
    plt.show()
    pprint.pprint(info)


# %%
mode = "winsorize"
lower_quantile = 0.01
window = 1000
min_periods = 10
info = collections.OrderedDict()
srs_out = sigp.process_outliers(
    srs, mode, lower_quantile, window=window, min_periods=min_periods, info=info
)
#
_analyze(srs_out)

# %%
mode = "winsorize"
lower_quantile = 0.01
upper_quantile = 0.90
window = 1000
min_periods = 10
info = collections.OrderedDict()
srs_out = sigp.process_outliers(
    srs,
    mode,
    lower_quantile,
    upper_quantile=upper_quantile,
    window=window,
    min_periods=min_periods,
    info=info,
)
#
_analyze(srs_out)

# %%
mode = "set_to_nan"
lower_quantile = 0.01
window = 1000
min_periods = 10
info = collections.OrderedDict()
srs_out = sigp.process_outliers(
    srs, mode, lower_quantile, window=window, min_periods=min_periods, info=info
)
#
_analyze(srs_out)

# %%
mode = "set_to_zero"
lower_quantile = 0.10
window = 1000
min_periods = 10
info = collections.OrderedDict()
srs_out = sigp.process_outliers(
    srs, mode, lower_quantile, window=window, min_periods=min_periods, info=info
)
#
_analyze(srs_out)

# %%
