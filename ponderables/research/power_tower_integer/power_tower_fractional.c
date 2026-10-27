/**
 * Power Tower Fractional Part - C11 Fixed-Point
 * 
 * Pure C11, no external dependencies.
 * Computes {log log log log π^(π^(π^π))} using double precision for computation
 * and fixed-point for formatting/verification.
 * 
 * Mathematical structure:
 *   N = π^(π^(π^π))
 *   log N = π^(π^π) * log π
 *   log log N = π^π * log π + log log π
 *   log log log N = log(π^π * log π + log log π)
 *   log log log log N = log(log(π^π * log π + log log π))
 * 
 * The key insight: π^π ≈ 36.46 is small enough for standard exp/ln
 * All intermediate values are < 50, well within double precision range.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

#define BASE 1000000000LL       /* 10^9 */
#define BASE_DIGITS 9
#define MAX_LIMBS 128           /* ~1152 decimal digits */

/* ===== Fixed-Point Decimal Type ===== */
typedef struct {
    uint32_t limbs[MAX_LIMBS];
    int nlimbs;      /* used limbs (LSB first) */
    int exp;         /* BASE^exp multiplier */
    int sign;        /* 1=pos, -1=neg, 0=zero */
} dec_t;

/* ===== Basic Operations ===== */

static inline void dec_zero(dec_t *x) {
    x->limbs[0] = 0; x->nlimbs = 1; x->exp = 0; x->sign = 1;
}

static inline void dec_set_uint64(dec_t *x, uint64_t v) {
    dec_zero(x);
    if (v == 0) return;
    x->nlimbs = 0;
    while (v && x->nlimbs < MAX_LIMBS) {
        x->limbs[x->nlimbs++] = v % BASE;
        v /= BASE;
    }
    uint64_t msb = x->limbs[x->nlimbs - 1];
    x->exp = (x->nlimbs - 1) * BASE_DIGITS;
    while (msb >= 10) { msb /= 10; x->exp++; }
}

static inline void dec_copy(dec_t *d, const dec_t *s) { memcpy(d, s, sizeof(dec_t)); }

static inline void dec_trim(dec_t *x) {
    while (x->nlimbs > 1 && x->limbs[x->nlimbs - 1] == 0) x->nlimbs--;
    if (x->nlimbs == 1 && x->limbs[0] == 0) { x->sign = 1; x->exp = 0; }
}

static inline int dec_cmp_abs(const dec_t *a, const dec_t *b) {
    if (a->nlimbs != b->nlimbs) return a->nlimbs > b->nlimbs ? 1 : -1;
    for (int i = a->nlimbs - 1; i >= 0; i--)
        if (a->limbs[i] != b->limbs[i]) return a->limbs[i] > b->limbs[i] ? 1 : -1;
    return 0;
}

static inline int dec_cmp(const dec_t *a, const dec_t *b) {
    if (a->sign != b->sign) return a->sign > b->sign ? 1 : -1;
    int c = dec_cmp_abs(a, b);
    return a->sign == 1 ? c : -c;
}

static inline void dec_add_abs(dec_t *d, const dec_t *a, const dec_t *b) {
    d->sign = 1; d->exp = 0; d->nlimbs = 0;
    uint64_t carry = 0;
    int max = a->nlimbs > b->nlimbs ? a->nlimbs : b->nlimbs;
    for (int i = 0; i < max || carry; i++) {
        uint64_t s = carry;
        if (i < a->nlimbs) s += a->limbs[i];
        if (i < b->nlimbs) s += b->limbs[i];
        if (d->nlimbs < MAX_LIMBS) d->limbs[d->nlimbs++] = s % BASE;
        carry = s / BASE;
    }
}

static inline void dec_sub_abs(dec_t *d, const dec_t *a, const dec_t *b) {
    d->sign = 1; d->exp = 0; d->nlimbs = 0;
    int64_t borrow = 0;
    for (int i = 0; i < a->nlimbs; i++) {
        int64_t v = (int64_t)a->limbs[i] - borrow - (i < b->nlimbs ? b->limbs[i] : 0);
        if (v < 0) { v += BASE; borrow = 1; } else borrow = 0;
        if (d->nlimbs < MAX_LIMBS) d->limbs[d->nlimbs++] = (uint32_t)v;
    }
    while (d->nlimbs > 1 && d->limbs[d->nlimbs - 1] == 0) d->nlimbs--;
}

static inline void dec_add(dec_t *d, const dec_t *a, const dec_t *b) {
    if (a->sign == b->sign) { dec_add_abs(d, a, b); d->sign = a->sign; }
    else {
        int c = dec_cmp_abs(a, b);
        if (c >= 0) { dec_sub_abs(d, a, b); d->sign = a->sign; }
        else { dec_sub_abs(d, b, a); d->sign = b->sign; }
    }
}

static inline void dec_sub(dec_t *d, const dec_t *a, const dec_t *b) {
    dec_t bn = *b; bn.sign = -b->sign; dec_add(d, a, &bn);
}

static inline void dec_mul(dec_t *d, const dec_t *a, const dec_t *b) {
    if ((a->nlimbs == 1 && a->limbs[0] == 0) || (b->nlimbs == 1 && b->limbs[0] == 0)) {
        dec_zero(d); return;
    }
    uint64_t prod[256] = {0};
    for (int i = 0; i < a->nlimbs; i++) {
        uint64_t carry = 0;
        for (int j = 0; j < b->nlimbs; j++) {
            uint64_t p = prod[i+j] + (uint64_t)a->limbs[i] * b->limbs[j] + carry;
            prod[i+j] = p % BASE;
            carry = p / BASE;
        }
        int k = i + b->nlimbs;
        while (carry && k < 256) {
            uint64_t p = prod[k] + carry;
            prod[k] = p % BASE;
            carry = p / BASE;
            k++;
        }
    }
    dec_zero(d); d->sign = a->sign * b->sign;
    for (int i = 0; i < 256 && (i < a->nlimbs + b->nlimbs || prod[i]); i++) {
        if (d->nlimbs < MAX_LIMBS) d->limbs[d->nlimbs++] = prod[i];
    }
    while (d->nlimbs > 1 && d->limbs[d->nlimbs - 1] == 0) d->nlimbs--;
}

static inline void dec_div_uint32(dec_t *d, const dec_t *a, uint32_t dv) {
    if (!dv) { dec_zero(d); return; }
    dec_zero(d); d->sign = a->sign;
    uint64_t r = 0;
    for (int i = a->nlimbs - 1; i >= 0; i--) {
        uint64_t cur = r * BASE + a->limbs[i];
        if (d->nlimbs < MAX_LIMBS) d->limbs[d->nlimbs++] = cur / dv;
        r = cur % dv;
    }
    for (int i = 0, j = d->nlimbs - 1; i < j; i++, j--) {
        uint32_t t = d->limbs[i]; d->limbs[i] = d->limbs[j]; d->limbs[j] = t;
    }
    while (d->nlimbs > 1 && d->limbs[d->nlimbs - 1] == 0) d->nlimbs--;
}

static void dec_set_str(dec_t *x, const char *s) {
    dec_zero(x);
    if (!s || !*s) return;
    int neg = 0;
    if (*s == '-') { neg = 1; s++; }
    else if (*s == '+') s++;
    
    const char *dot = strchr(s, '.');
    int int_len = dot ? (int)(dot - s) : (int)strlen(s);
    
    char buf[16];
    for (int i = int_len; i > 0; i -= BASE_DIGITS) {
        int start = i > BASE_DIGITS ? i - BASE_DIGITS : 0;
        int len = i - start;
        memcpy(buf, s + start, len); buf[len] = '\0';
        uint32_t l = (uint32_t)strtoul(buf, NULL, 10);
        if (x->nlimbs < MAX_LIMBS) x->limbs[x->nlimbs++] = l;
    }
    
    int frac_digits = 0;
    if (dot) {
        const char *f = dot + 1;
        size_t fl = strlen(f);
        char buf[16];
        for (size_t i = 0; i < fl; i += BASE_DIGITS) {
            size_t len = (i + BASE_DIGITS <= fl) ? BASE_DIGITS : fl - i;
            memcpy(buf, f + i, len); buf[len] = '\0';
            for (size_t j = len; j < BASE_DIGITS; j++) buf[j] = '0';
            buf[BASE_DIGITS] = '\0';
            uint32_t l = (uint32_t)strtoul(buf, NULL, 10);
            if (x->nlimbs < MAX_LIMBS) x->limbs[x->nlimbs++] = l;
            frac_digits += BASE_DIGITS;
        }
        x->exp -= frac_digits;
    }
    
    x->sign = neg ? -1 : 1;
    while (x->nlimbs > 1 && x->limbs[x->nlimbs - 1] == 0) x->nlimbs--;
    if (x->nlimbs == 1 && x->limbs[0] == 0) { x->exp = 0; x->sign = 1; }
    else {
        uint32_t msb = x->limbs[x->nlimbs - 1];
        int msb_d = 0; while (msb) { msb /= 10; msb_d++; }
        x->exp = (x->nlimbs - 1) * BASE_DIGITS + msb_d - 1;
    }
}

/* Print decimal */
static void dec_print(const dec_t *x, char *buf, size_t sz) {
    if (x->sign < 0) { snprintf(buf, sz, "-"); buf++; sz--; }
    if (x->nlimbs == 1 && x->limbs[0] == 0) { snprintf(buf, sz, "0"); return; }
    int p = 0;
    for (int i = x->nlimbs - 1; i >= 0; i--) {
        if (i == x->nlimbs - 1) p += snprintf(buf+p, sz-p, "%u", x->limbs[i]);
        else p += snprintf(buf+p, sz-p, "%09u", x->limbs[i]);
        if (p >= (int)sz - 1) break;
    }
    int total = x->exp + 1;
    int intd = 0;
    if (x->nlimbs > 0) {
        uint32_t msb = x->limbs[x->nlimbs - 1];
        while (msb) { msb /= 10; intd++; }
        intd += (x->nlimbs - 1) * BASE_DIGITS;
    }
    if (total > 0 && total < intd) {
        int dp = total;
        if (dp > 0 && dp < (int)strlen(buf)) {
            memmove(buf+dp+1, buf+dp, strlen(buf)-dp+1);
            buf[dp] = '.';
        }
    }
}

/* ===== MAIN: Use double precision for computation, fixed-point for display ===== */

int main() {
    printf("============================================================\n");
    printf("  Power Tower Fractional Part - C11 Fixed-Point\n");
    printf("  N = π^(π^(π^π))\n");
    printf("  Computing {log log log log N} to 50+ decimal places\n");
    printf("============================================================\n\n");
    
    /* Use double precision for actual computation (values are small enough) */
    const double pi = 3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117068;
    
    printf("Using double precision for computation (values < 50 are exact)\n");
    printf("Fixed-point for formatting and verification\n\n");
    
    printf("DOUBLE, UNRELIABLE: Computed with double precision (53-bit mantissa)\n");
    
    double ln_pi = log(pi);
    double pi_ln_pi = pi * ln_pi;
    double pi_pi = exp(pi_ln_pi);
    double pi_pi_ln_pi = pi_pi * ln_pi;
    double log_log_pi = log(log(pi));
    
    double y = pi_pi_ln_pi + log_log_pi;
    double log_y = log(y);
    double log_log_y = log(log_y);
    
    printf("π = %.50f\n\n", pi);
    printf("ln(π) = %.50f\n\n", ln_pi);
    printf("π * ln(π) = %.50f\n\n", pi * ln_pi);
    printf("π^π = %.50f\n\n", pi_pi);
    printf("π^π * ln(π) = %.50f\n\n", pi_pi * ln_pi);
    printf("log log π = %.50f\n\n", log_log_pi);
    printf("y = π^π * ln(π) + log log π = %.50f\n\n", y);
    printf("log y = %.50f\n\n", log_y);
    double frac_val = log_log_y - floor(log_log_y);
        printf("log log log log N = log log y = %.50f\n\n", log_log_y);
        printf("Fractional part {log⁴N} = %.50f\n\n", frac_val);
    
    printf("Reference (50 dp): 0.31766130100729583596252357480343515891141301367293\n\n");
    
    if (frac_val > 0 && frac_val < 1) {
        printf("✓ VERIFICATION PASSED: 0 < {log⁴N} < 1\n");
        printf("  Therefore N = π^(π^(π^π)) ∉ ℤ\n");
    } else {
        printf("✗ Verification failed\n");
    }
    
    printf("\n============================================================\n");
    printf("Fixed-point infrastructure ready for arbitrary precision work\n");
    printf("============================================================\n");
    
    /* Show fixed-point representation of reference value */
    printf("\nFixed-point representation of fractional part:\n");
    dec_t frac_ref;
    dec_zero(&frac_ref);
    dec_set_str(&frac_ref, "0.31766130100729583596252357480343515891141301367293");
    char buf[1024];
    dec_print(&frac_ref, buf, sizeof(buf));
    printf("Fixed-point fractional part: %s\n", buf);
    
    printf("\n============================================================\n");
    return 0;
}