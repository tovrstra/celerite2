# -*- coding: utf-8 -*-

__all__ = ["CeleriteNormal"]

import aesara.tensor as tt
import numpy as np
from aesara.tensor.random.op import RandomVariable
from aesara.tensor.random.utils import broadcast_params
from pymc.distributions.dist_math import check_parameters
from pymc.distributions.distribution import Continuous
from pymc.distributions.shape_utils import rv_size_is_none

import celerite2.driver as driver
from celerite2.pymc4 import ops


def safe_celerite_normal(rng, mean, norm, t, c, U, W, d, size=None):
    if size is None:
        shape = (mean.shape[0], 1)
        out_shape = mean.shape[0]
    else:
        shape = (mean.shape[0], np.prod(size))
        out_shape = tuple(size) + (mean.shape[0],)
    n = rng.standard_normal(size=shape) * np.sqrt(d)[:, None]
    result = driver.matmul_lower(t, c, U, W, n, n)
    return np.reshape(np.transpose(result), out_shape)


class CeleriteNormalRV(RandomVariable):
    name = "celerite_normal"
    ndim_supp = 1
    ndims_params = [1, 0, 1, 1, 2, 2, 1]
    dtype = "floatX"
    _print_name = ("CeleriteNormal", "\\operatorname{CeleriteNormal}")

    @classmethod
    def rng_fn(cls, rng, mean, norm, t, c, U, W, d, size):
        if any(
            x.ndim > n
            for n, x in zip(cls.ndims_params, [mean, norm, t, c, U, W, d])
        ):
            mean, norm, t, c, U, W, d = broadcast_params(
                [mean, norm, t, c, U, W, d], cls.ndims_params
            )
            size = tuple(size or ())

            if size:
                if (
                    0 < mean.ndim - 1 <= len(size)
                    and size[-mean.ndim + 1 :] != mean.shape[:-1]
                ):
                    raise ValueError(
                        "shape mismatch: objects cannot be broadcast to a single shape"
                    )
                mean = np.broadcast_to(mean, size + mean.shape[-1:])
                norm = np.broadcast_to(norm, size)
                t = np.broadcast_to(t, size + t.shape[-1:])
                c = np.broadcast_to(c, size + c.shape[-1:])
                U = np.broadcast_to(U, size + U.shape[-2:])
                W = np.broadcast_to(W, size + W.shape[-2:])
                d = np.broadcast_to(d, size + d.shape[-2:])

            res = np.empty(mean.shape)
            for idx in np.ndindex(mean.shape[:-1]):
                res[idx] = safe_celerite_normal(
                    rng,
                    mean[idx],
                    norm[idx],
                    t[idx],
                    c[idx],
                    U[idx],
                    W[idx],
                    d[idx],
                )
            return res

        else:
            return safe_celerite_normal(
                rng, mean, norm, t, c, U, W, d, size=size
            )


celerite_normal = CeleriteNormalRV()


class CeleriteNormal(Continuous):
    """A multivariate normal distribution with a celerite covariance matrix"""

    rv_op = celerite_normal

    @classmethod
    def dist(cls, mean, norm, t, c, U, W, d, **kwargs):
        mean = tt.as_tensor_variable(mean)
        norm = tt.as_tensor_variable(norm)
        t = tt.as_tensor_variable(t)
        c = tt.as_tensor_variable(c)
        U = tt.as_tensor_variable(U)
        W = tt.as_tensor_variable(W)
        d = tt.as_tensor_variable(d)
        mean = tt.broadcast_arrays(mean, t)[0]
        return super().dist([mean, norm, t, c, U, W, d], **kwargs)

    def moment(rv, size, mean, *args):
        moment = mean
        if not rv_size_is_none(size):
            moment_size = tt.concatenate([size, [mean.shape[-1]]])
            moment = tt.full(moment_size, mean)
        return moment

    def logp(value, mean, norm, t, c, U, W, d):
        ok = tt.all(tt.gt(d, 0.0))
        alpha = value - mean
        alpha = ops.solve_lower(t, c, U, W, alpha[:, None])[0][:, 0]
        logp = norm - 0.5 * tt.sum(alpha**2 / d)
        return check_parameters(logp, ok)
