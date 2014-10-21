from ref_resolver import resolve_pointer

def fn_iadd(act):
    return int(act["lhs"]) + int(act["rhs"])

def fn_isub(act):
    return int(act["lhs"]) - int(act["rhs"])

def fn_imul(act):
    return int(act["lhs"]) * int(act["rhs"])

def fn_idiv(act):
    return int(act["lhs"]) / int(act["rhs"])


def fn_fadd(act):
    return float(act["lhs"]) + float(act["rhs"])

def fn_fsub(act):
    return float(act["lhs"]) - float(act["rhs"])

def fn_fmul(act):
    return float(act["lhs"]) * float(act["rhs"])

def fn_fdiv(act):
    return float(act["lhs"]) / float(act["rhs"])


def fn_noop(act):
    return act


def fn_gt(act):
    return act["lhs"] > act["rhs"]

def fn_gte(act):
    return act["lhs"] >= act["rhs"]

def fn_lt(act):
    return act["lhs"] < act["rhs"]

def fn_lte(act):
    return act["lhs"] <= act["rhs"]

def fn_format(act):
    act["format"].format(**act)

std_funcs = {
    "noop": fn_noop,
    "+": fn_fadd,
    "-": fn_fsub,
    "*": fn_fmul,
    "/": fn_fdiv,
    "iadd": fn_iadd,
    "isub": fn_isub,
    "imul": fn_imul,
    "idiv": fn_idiv,
    ">": fn_gt,
    ">=": fn_gte,
    "<": fn_lt,
    "<=": fn_lte,
    "format": fn_format
}

def eval_jx(available_fn, document, m):
    if isinstance(m, dict):
        em = {k: eval_jx(available_fn, document, v) for k,v in m.items()}
        if "$fn" in em:
            return available_fn[em["$fn"]](em)
        if "$ref" in em:
            return eval_jx(available_fn, document, resolve_pointer(document, em["$ref"]))
        else:
            return em
    elif isinstance(m, list):
        return [eval_jx(available_fn, document, i) for i in m]
    else:
        return m
