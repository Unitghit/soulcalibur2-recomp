// SPDX-License-Identifier: GPL-3.0-or-later
#ifdef NDEBUG
#undef NDEBUG
#endif
#include "../guest/link_hair.h"
#include <cassert>
#include <cstdio>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
int main(int argc, char **) {
    guest::Bytes model(0x80 + 17 * 0x50, 0x5a);
    std::memcpy(model.data(), "VMX.", 4);
    guest::put16(model, 0x14, 17);
    guest::put32(model, 0x1c, 0x80);
    for (size_t i : {3u, 4u}) guest::put32(model, 0x80 + i * 0x50, 0x08000002);
    const auto before = model;
    guest::link_hair_two_sided(model);
    auto expected = before;
    for (size_t i : {3u, 4u}) guest::put32(expected, 0x80 + i * 0x50, 2);
    assert(model == expected);
    guest::link_hair_two_sided(model);
    assert(model == expected);
    for (unsigned bad : {0u, 1u, 2u}) {
        auto broken = before;
        if (bad == 0) guest::put16(broken, 0x14, 16);
        if (bad == 1) guest::put32(broken, 0x80 + 4 * 0x50, 7);
        if (bad == 2) broken.resize(0x80 + 4 * 0x50);
        const auto unchanged = broken;
        bool rejected = false;
        try { guest::link_hair_two_sided(broken); } catch (const guest::Error &) { rejected = true; }
        assert(rejected && broken == unchanged);
    }
    if (argc > 1) {
#ifdef _WIN32
        _setmode(_fileno(stdout), _O_BINARY);
#endif
        std::fwrite(model.data(), 1, model.size(), stdout);
    } else std::puts("PASS: scoped hair flags, idempotence, malformed input and atomic validation");
}
