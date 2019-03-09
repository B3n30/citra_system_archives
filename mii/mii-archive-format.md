# 3DS Mii Components Archive

The archive title ID is 0004009B 00010202. The archive contains a single file `CFL_Res.data`, whose format is described below

## Header

| Offset | Type | Description|
| --- | --- | --- |
| `0x00000000` | `u16` | Section count `X` ( = `20`) |
| `0x00000002` | `u16` | ? ( = `0x0509`) |
| `0x00000004` | `u32[X]` | Section offsets, relative to the file beginning|

The file begins with this header, followed by `X = 20` sections.

## Section

Each section contains one category of Mii components, described as follows:

0. Goatee models
1. Hair accessory models
2. Face models
3. Scalp models
4. Glasses canvas models
5. Hair models
6. Face canvas models
7. Nose canvas models
8. Nose models
9. Hair accessory textures
10. Eye textures
11. Eyebrow textures
12. Goatee textures
13. Wrinkle textures
14. Makeup textures
15. Glasses textures
16. Mole textures
17. Mouth textures
18. Mustache textures
19. Nose textures

As can be seen, a section contains items of either the model format or the texture format. The detailed description of these two formats are below

Target models that different textures apply to are:
 - Face A: 10, 11, 16, 17, 18 → 6
 - Face B: 12, 13, 14 → 2
 - Glasses: 15 → 4
 - Nose: 19 → 7

Components that are grouped together (meaning the same item index for components in the same group is always chosen):
 - Hair: (1, 3, 5, 9)
 - Face: (2, 6)
 - Nose: (7, 8, 19)


### Section Header

| Offset | Type | Description|
| --- | --- | --- |
| `0x00000000` | `u16` | Item count `Y` |
| `0x00000002` | `u16` | Maximum size for one item in this section|
| `0x00000004` | `{u22, u10}[Y]` | Bitfields. Lower 22-bits are item offsets, relative to the *end* of the section header. Upper 10-bits are redirection index.
|`4 + Y * 4`| `u32` | Offset to the *end* of this section (i.e. the end of the last item), relative to the *end* of the section header|

A section begins with this section header, followed by `Y` items. And item `i` can have 0 size, in which case `Offset[i] == Offset[i + 1]`. The redirection index has no effecto when it equals zero. A non-zero redirection index `R` for item `i` means the item `i` refers to the same content as item `R - 1`, i.e. the offset for item `i` should be `Offset[R - 1]` instead of `Offset[i]`.

### Model Item Format

| Offset | Type | Description|
| --- | --- | --- |
| `0x00000000` | `vec3<float>` | Hair coordinates. Only present for section 2
| `0x0000000C` | `vec3<float>` | Nose & glasses coordinates. Only present for section 2|
| `0x00000018` | `vec3<float>` | Goatee coordinates. Only present for section 2
|||
| `0x00000000` | `vec3<float>` | Hat A euler angles. Only present for section 5 |
| `0x0000000C` | `vec3<float>` | Hat A coordinates. Only present for section 5 |
| `0x00000018` | `vec3<float>` | Hat B euler angles. Only present for section 5 |
| `0x00000024` | `vec3<float>` | Hat B coordinates. Only present for section 5 |
| `0x00000030` | `vec3<float>` | Hat C euler angles. Only present for section 5 |
| `0x0000003C` | `vec3<float>` | Hat C coordinates. Only present for section 5 |
|||
| `0x00/24/48+0x00` | `u16` | Vertex count (`C`) |
| `0x00/24/48+0x02` | `u16` | Normal count (`N` = `0`, `1` or `C`)|
| `0x00/24/48+0x04` | `u16` | Texcoord count (`T` = `0`, `1` or `C`)|
| `0x00/24/48+0x06` | `u16` | Index list count (`I` = `0` or `1`)|
| `0x00/24/48+0x08` | `{`<br>`vec3<s16>, `<br>`(vec3<s16>), `<br>`(vec2<s16>)`<br>`}[C]` | Vertex list. Each vertex contains coordinates, normal and texture coordinates. However, the normal field is there only if `N == C`. Similarly, the texcoord field is there only if `T == C`. The coordinates and the normals are scaled by 256, while the texture coordinates are scaled by 8192|
|||
| ... | `vec3<s16>` | Common normal for all vertices, scaled by 256. Present only if `N == 1`
| ... | `vec2<s16>` | Common texcoord for all vertices, scaled by 8192. Present only if `T == 1`|
|||
| ... | `u16` | ? ( = `4`). Present only if `I == 1`|
| ... | `u16` | Index count (`J`). Present only if `I == 1`|
| ... | `u8[J]` | Index list. Present only if `I == 1`|
|||
| ... | `{`<br>`u4 ymax, `<br>`u4 ymin, `<br>`u4 xmax, `<br>`u4 xmin`<br>`}[J/3]` | Bitfields, representing a rectangular coverage of each triangle in the texture space divided into 16x16 grids. Only present for section 6.
|||
| ... | ... | Padding for 4-byte alignment

### Texture Item Format

| Offset | Type | Description|
| --- | --- | --- |
| 0x00000000 | u16 | Width
| 0x00000002 | u16 | Height
| 0x00000004 | u8 | Mipmap level (always `1`)
| 0x00000005 | u8 | Format
| 0x00000006 | u8 | U Wrapping Mode
| 0x00000007 | u8 | V Wrapping Mode
| 0x00000008 | ... | Texture Data

Supported texture format a listed below. This table is extracted from game code that translates the format to PICA format. Only a few of them are used in the archive:

0. I4
1. I8
2. A4
3. A8
4. IA4
5. IA8
6. RG8
7. RGB565
8. RGB8
9. RGB5A1
10. RGBA4
11. RGBA8
12. ETC1
13. ETC1A4

Supported wrapping mode are

0. Clamp to edge
1. Repeat
2. Mirrored repeat

The texture data has an actual size of `MWidth * MHeight * BitPerPixel / 8`, where `MWidth` and `MHeight` are *the smallest power of 2* greater than or equal to `Width` and `Height`, repectively.
