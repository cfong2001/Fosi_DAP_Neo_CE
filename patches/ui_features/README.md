# Bluetooth shortcut and lock-screen information

Both ship in the Standard image, composed by the full build
([`../full/README.md`](../full/README.md)):

- Patch 0032: a long press of Power turns Bluetooth on or off. The routine
  lives in the shared gap tail; [`build/`](build/) builds it standalone.
- Patch 0033: with hold on, the lock screen shows the track title and elapsed
  and total time. The routine lives in the module 31 extension;
  [`lockscreen_build/`](lockscreen_build/lockscreen_build.md) builds and
  emulates it standalone.

- [`ui_features.md`](ui_features.md): the hold-state pins, the overlay residency proof and the dispatcher hook.
- [`../bt_auto_off/`](../bt_auto_off/README.md): the separate Bluetooth auto-off build option.
