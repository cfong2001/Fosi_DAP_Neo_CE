# Theater mode and safer track titles

Theater mode ships in the Standard image, composed by the full build
([`../full/README.md`](../full/README.md)): hooks 0100 to 0104, the no-art
reset 0045 and 0046, and its routine in the shared gap tail. The player
background takes the average colour of the top third of the album art, mixed
55% toward black (dark theme) or 75% toward paper (light theme); tracks
without art use the theme default.

- [`build/`](build/): the standalone theater variant (theater alone in the
  gap tail) and its emulation tests. Its README describes that variant, which
  is not the Standard image.
- [`text/`](text/): the player title-copy bounds repair (title-copy and
  title-suffix), also shipped in the Standard image.
- `frame_average.c`: the averaging routine, with host tests.
- [`../design_refresh_v2/theater_mode.md`](../design_refresh_v2/theater_mode.md): the design.
