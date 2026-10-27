import Lake

open Lake DSL

package power_tower_proof where
  packagesDir := ".lake/packages"

  require mathlib from git "https://github.com/leanprover-community/mathlib4" @ "v4.13.0"