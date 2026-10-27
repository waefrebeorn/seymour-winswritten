# Power Tower Fractional Part - Build Configuration

# Build with double precision (always works, but INSUFFICIENT for actual proof)
#   make double
# 
# Build with MPFR arbitrary precision (requires libmpfr-dev)
#   make mpfr
# 
# Default: double precision with warning
.PHONY: all double mpfr clean

CC = gcc
CFLAGS = -std=c11 -O3 -Wall -Wextra -pedantic
LDFLAGS = -lm

# Double precision (no external deps)
double: CFLAGS += -DDOUBLE_PRECISION
double: power_tower_fractional
	@echo "Built with double precision (WARNING: insufficient for proof)"

# MPFR arbitrary precision (requires libmpfr-dev, libgmp-dev)
mpfr: CFLAGS += -DHAVE_MPFR
mpfr: LDFLAGS += -lmpfr -lgmp
mpfr: power_tower_fractional
	@echo "Built with MPFR arbitrary precision"

# Main target
power_tower_fractional: power_tower_fractional.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f power_tower_fractional

# Install MPFR on Debian/Ubuntu:
#   sudo apt-get install libmpfr-dev libgmp-dev

# Test run (double precision):
#   make double && ./power_tower_fractional

# Test run (MPFR, when available):
#   make mpfr && ./power_tower_fractional

# Verify with Python (uses pre-computed reference values):
#   python3 verify_fractional_part.py