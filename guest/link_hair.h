// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef SC2_GUEST_LINK_HAIR_H
#define SC2_GUEST_LINK_HAIR_H
#include "bytes.h"
namespace guest {
// Compatibility treatment for the two outer-hair passes in Link's four
// supported US costumes. Single-sided Xbox rendering drops portions of these
// thin surfaces. Keep the authored normals, lighting, alpha and triangle order;
// make only these materials two-sided, just like his other hair passes.
inline void link_hair_two_sided(Bytes &model)
{
    if (!starts(model, "VMX.", 4) || le16(model, 0x14) != 17)
        throw Error("unexpected Link costume material layout");
    const size_t base = le32(model, 0x1c);
    for (size_t material : {3u, 4u}) {
        const size_t at = base + material * 0x50;
        const uint32_t flags = le32(model, at);
        if (flags != 0x08000002u && flags != 2u)
            throw Error("unexpected Link hair material flags");
    }
    for (size_t material : {3u, 4u}) put32(model, base + material * 0x50, 2u);
}
}
#endif
