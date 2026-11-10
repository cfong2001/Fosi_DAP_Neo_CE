// The CS43198 digital filter option (patches/dac_filter/). Each choice
// is one byte patch at the DAC init's mode-0 immediate (exec 0x03051814),
// so a build takes at most one. tests/builder.test.mjs keeps these
// entries equal to the patch files and to build.py --dac-filter output.
const site = {module: 0, region: "code", address: 0x03051814, expect: "0221"};

export const DAC_FILTERS = [
  {id: "stock", label: "Fast roll-off, low latency (stock)", patch: null},
  {id: "fast-linear-phase", label: "Fast roll-off, linear phase",
   patch: {...site, index: 34, name: "dac-filter-fast-linear-phase", replace: "4221"}},
  {id: "slow-low-latency", label: "Slow roll-off, low latency",
   patch: {...site, index: 35, name: "dac-filter-slow-low-latency", replace: "8221"}},
  {id: "slow-linear-phase", label: "Slow roll-off, linear phase",
   patch: {...site, index: 36, name: "dac-filter-slow-linear-phase", replace: "c221"}},
  {id: "nos", label: "Non-oversampling (NOS)",
   patch: {...site, index: 37, name: "dac-filter-nos", replace: "2221"}},
];

export function dacFilterPatches(id) {
  const choice = DAC_FILTERS.find(f => f.id === id);
  if (!choice) throw new Error("unknown DAC filter: " + id);
  return choice.patch ? [choice.patch] : [];
}
