#!/usr/bin/env python3
"""Quiet scan order only: nearest to the 1h average first. Entry rules unchanged."""
import os
import shutil
import py_compile

TARGET = "main.py"
BACKUP = "main.py.bak_quietrank"

OLD = """    movers.sort(reverse=True)
    armed_names = [s for s, info in _body_arm.items() if info.get("side") == quiet_side]
"""

NEW = """    ranked = []
    for row in movers:
        sym = row[1]
        gap = 9e9
        try:
            k1 = await get_futures_klines_cached(symbol=sym, interval="1h", limit=40, closed_only=True)
            if k1 and len(k1) >= 22:
                c1 = np.array([float(x[4]) for x in k1], dtype=float)
                ema1 = float(talib.EMA(c1, 21)[-1])
                px = float(c1[-1])
                if px > 0 and ema1 > 0:
                    gap = abs(px - ema1) / px
        except Exception:
            gap = 9e9
        ranked.append((gap, row))
    ranked.sort(key=lambda item: item[0])
    movers = [row for _, row in ranked]
    if ranked and ranked[0][0] < 9e8:
        near = ", ".join(f"{row[1]} {gap * 100:.1f}%" for gap, row in ranked[:3])
        logger.info(f"\\U0001f4e1 Quiet rank | closest {near}")
    armed_names = [s for s, info in _body_arm.items() if info.get("side") == quiet_side]
"""


def fail(msg):
    shutil.copy2(BACKUP, TARGET)
    print(msg)
    print(f"restored from {BACKUP} — bot file was not changed")


def main():
    if not os.path.exists(TARGET):
        print(f"STOPPED missing {TARGET}")
        return
    shutil.copy2(TARGET, BACKUP)
    text = open(TARGET, encoding="utf-8").read().replace("\r\n", "\n").replace("\r", "\n")
    if "Quiet rank | closest" in text:
        fail("STOPPED quiet rank is already in this file")
        return
    n = text.count(OLD)
    if n != 1:
        fail(f"STOPPED sort count={n}")
        return
    text = text.replace(OLD, NEW, 1)
    open(TARGET, "w", encoding="utf-8").write(text)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        fail(f"STOPPED compile: {e}")
        return
    print("DONE pieces=1")
    print(f"backup={BACKUP}")


if __name__ == "__main__":
    main()
