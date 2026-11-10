// The Bluetooth auto-off option (patches/bt_auto_off/). Stock turns
// Bluetooth off after 5 minutes without a connection; each choice is one
// patch in module 0's supervisor, so a build takes at most one.
// tests/builder.test.mjs keeps these entries equal to the patch files and
// to build.py --bt-auto-off output.
export const BT_AUTO_OFF = [
  {id: "stock", label: "After 5 minutes without a connection (stock)", patch: null},
  {id: "10min", label: "After 10 minutes without a connection",
   patch: {index: 38, name: "bt-auto-off-10min", module: 0, region: "code",
           address: 0x030661e0, expect: "47f23051", replace: "4ef66021"}},
  {id: "never", label: "Never: stays on until you turn it off",
   patch: {index: 39, name: "bt-auto-off-never", module: 0, region: "code",
           address: 0x030661e6, expect: "7ff66baf", replace: "fff76bbf"}},
];

export function btAutoOffPatches(id) {
  const choice = BT_AUTO_OFF.find(c => c.id === id);
  if (!choice) throw new Error("unknown Bluetooth auto-off choice: " + id);
  return choice.patch ? [choice.patch] : [];
}
