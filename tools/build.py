# -*- coding: utf-8 -*-
"""
重打 iOS 韓文槽的繁體中文語言包。

來源：
  ghcruise/LimbusCompany-IOS-Localization  最新 release  → manifest 基底 + 墊檔
  LimbusTraditionalMandarin/storyline       最新 release  → 繁中譯本

產出（寫在 repo 根目錄，供 jsDelivr 取用）：
  manifest.json     只改 KR 條目雜湊，JP/EN 維持官方原值
  localize_kr.zip   韓文槽全量替換包
  sources.json      本次用的上游版本，供下次比對

替換表 tools/subtable.json 來自實機探針，不是推測：
iOS 韓文槽字型缺 76 個繁體字（見 tools/missing_confirmed.json），
字型無法替換（manifest 只含 Localize JSON，且 iOS 沒有官方自訂語言功能），
因此必須把那 76 字換成字型有的等價字。
"""
import json, zipfile, hashlib, os, io, sys, collections, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
WORK = os.path.join(ROOT, ".work")

GH_API = "https://api.github.com/repos/ghcruise/LimbusCompany-IOS-Localization/releases/latest"
LTM_INDEX = "https://gist.githubusercontent.com/kimght/322a2779922ab5a5f96ff7f7dc3f8e82/raw/localizations.json"


def fetch(url, dest=None):
    req = urllib.request.Request(url, headers={"User-Agent": "limbus-hant-builder"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    if dest:
        open(dest, "wb").write(data)
    return data


def main():
    os.makedirs(WORK, exist_ok=True)

    rel = json.loads(fetch(GH_API))
    gh_tag = rel["tag_name"]
    assets = {a["name"]: a["browser_download_url"] for a in rel["assets"]}

    ltm = next(l for l in json.loads(fetch(LTM_INDEX))["localizations"] if l["id"] == "hant-LTM")
    ltm_ver, ltm_url = ltm["version"], ltm["url"]

    prev = {}
    spath = os.path.join(ROOT, "sources.json")
    if os.path.exists(spath):
        prev = json.load(open(spath, encoding="utf-8"))

    print(f"ghcruise : {prev.get('ghcruise', '-')} -> {gh_tag}")
    print(f"LTM      : {prev.get('ltm', '-')} -> {ltm_ver}")

    if prev.get("ghcruise") == gh_tag and prev.get("ltm") == ltm_ver and "--force" not in sys.argv:
        print("上游皆無更新，跳過")
        return 0

    fetch(assets["manifest.json"], f"{WORK}/base_manifest.json")
    fetch(assets["localize_jp.zip"], f"{WORK}/ios_jp.zip")
    fetch(ltm_url, f"{WORK}/hant.zip")

    manifest = json.load(open(f"{WORK}/base_manifest.json", encoding="utf-8"))
    zh = zipfile.ZipFile(f"{WORK}/hant.zip")
    zi = zipfile.ZipFile(f"{WORK}/ios_jp.zip")
    hant = {os.path.basename(n): n for n in zh.namelist() if n.endswith(".json")}
    ios = {os.path.basename(n): n for n in zi.namelist() if n.endswith(".json")}

    sub = json.load(open(f"{TOOLS}/subtable.json", encoding="utf-8"))
    WORD, CHAR = sub["word"], sub["char"]
    TRANS = str.maketrans(CHAR)
    confirmed = set(json.load(open(f"{TOOLS}/missing_confirmed.json", encoding="utf-8")))

    src = collections.Counter()
    zpath = os.path.join(ROOT, "localize_kr.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zo:
        for f in [x for x in manifest["Files"] if "/kr/" in x]:
            rel_path = f.split("/Localize/")[1]
            stem = os.path.basename(rel_path)[3:]

            if stem in hant:
                t = zh.read(hant[stem]).decode("utf-8")
                for a, b in WORD.items():
                    t = t.replace(a, b)
                data = t.translate(TRANS).encode("utf-8")
                src["LTM 繁中"] += 1
            elif ("JP_" + stem) in ios:
                data = zi.read(ios["JP_" + stem])
                src["ghcruise 墊檔"] += 1
            else:
                data = b"{}"
                src["空檔"] += 1

            zo.writestr("LocalizeTemp_" + rel_path, data)
            manifest["Files"][f] = {"Hash": hashlib.md5(data).hexdigest(),
                                    "Size": len(data), "Crc": 0}

    # 壓掉排版：jsDelivr 會再 gzip，實際傳輸約 192KB
    mpath = os.path.join(ROOT, "manifest.json")
    open(mpath, "w", encoding="utf-8").write(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))

    # 驗證
    base = json.load(open(f"{WORK}/base_manifest.json", encoding="utf-8"))["Files"]
    zc = zipfile.ZipFile(zpath)
    left = collections.Counter()
    for n in zc.namelist():
        left.update(c for c in zc.read(n).decode("utf-8", "ignore") if c in confirmed)
    kr = [f for f in manifest["Files"] if "/kr/" in f]
    badhash = sum(1 for f in kr
                  if hashlib.md5(zc.read("LocalizeTemp_" + f.split("/Localize/")[1])).hexdigest()
                  != manifest["Files"][f]["Hash"])
    touched = sum(1 for f, v in manifest["Files"].items() if "/kr/" not in f and base[f] != v)

    print(f"來源分布 : {dict(src)}")
    print(f"殘留缺字 : {sum(left.values())} {dict(left) or ''}")
    print(f"KR 雜湊不符 : {badhash}")
    print(f"誤改到的非 KR 條目 : {touched}")
    print(f"manifest {os.path.getsize(mpath):,} bytes / zip {os.path.getsize(zpath):,} bytes")

    if sum(left.values()) or badhash or touched:
        print("驗證失敗，不輸出", file=sys.stderr)
        return 1

    json.dump({"ghcruise": gh_tag, "ltm": ltm_ver}, open(spath, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("BUILD_CHANGED=1")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
