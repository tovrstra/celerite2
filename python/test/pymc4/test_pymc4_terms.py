# -*- coding: utf-8 -*-

from functools import partial

import numpy as np
import pytest

pytest.importorskip("celerite2.pymc4")

try:
    from celerite2 import terms as pyterms
    from celerite2.pymc4 import terms
    from celerite2.testing import check_tensor_term
except (ImportError, ModuleNotFoundError):
    pass
else:
    compare_terms = partial(check_tensor_term, lambda x: x.eval())


def test_complete_implementation():
    x = np.linspace(-10, 10, 500)
    for name in pyterms.__all__:
        if name == "OriginalCeleriteTerm":
            continue
        term = getattr(terms, name)
        if name.startswith("Term"):
            continue
        pyterm = getattr(pyterms, name)
        args = pyterm.get_test_parameters()
        term = term(**args)
        pyterm = pyterm(**args)
        np.testing.assert_allclose(
            term.get_value(x).eval(), pyterm.get_value(x)
        )


@pytest.mark.parametrize(
    "name,args",
    [
        ("RealTerm", dict(a=1.5, c=0.3)),
        ("ComplexTerm", dict(a=1.5, b=0.7, c=0.3, d=0.1)),
        ("SHOTerm", dict(S0=1.5, w0=2.456, Q=0.1)),
        ("SHOTerm", dict(S0=1.5, w0=2.456, Q=3.4)),
        ("SHOTerm", dict(sigma=1.5, w0=2.456, Q=3.4)),
        ("SHOTerm", dict(sigma=1.5, rho=2.456, Q=3.4)),
        ("SHOTerm", dict(S0=1.5, rho=2.456, tau=0.5)),
        ("Matern32Term", dict(sigma=1.5, rho=3.5)),
        ("RotationTerm", dict(sigma=1.5, Q0=2.1, dQ=0.5, period=1.3, f=0.7)),
    ],
)
def test_base_terms(name, args):
    term = getattr(terms, name)(**args)
    pyterm = getattr(pyterms, name)(**args)
    compare_terms(term, pyterm)

    if hasattr(term, "coefficients"):
        compare_terms(terms.TermDiff(term), pyterms.TermDiff(pyterm))
        compare_terms(
            terms.TermConvolution(term, 0.5),
            pyterms.TermConvolution(pyterm, 0.5),
        )

    term0 = terms.SHOTerm(S0=1.0, w0=0.5, Q=1.5)
    pyterm0 = pyterms.SHOTerm(S0=1.0, w0=0.5, Q=1.5)
    compare_terms(term + term0, pyterm + pyterm0)
    compare_terms(term * term0, pyterm * pyterm0)

    term0 = terms.SHOTerm(S0=1.0, w0=0.5, Q=0.2)
    pyterm0 = pyterms.SHOTerm(S0=1.0, w0=0.5, Q=0.2)
    compare_terms(term + term0, pyterm + pyterm0)
    compare_terms(term * term0, pyterm * pyterm0)


def test_opt_error():
    import aesara.tensor as at
    from aesara import config, function, grad

    x = np.linspace(0, 5, 10)
    diag = np.full_like(x, 0.2)

    with config.change_flags(on_opt_error="raise"):
        arg = at.scalar()
        arg.tag.test_value = 0.5
        matrices = terms.SHOTerm(S0=1.0, w0=0.5, Q=arg).get_celerite_matrices(
            x, diag
        )
        function([arg], grad(sum(at.sum(m) for m in matrices), [arg]))(0.5)
