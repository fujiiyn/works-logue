"use client";

import { useEffect, useState } from "react";

/**
 * CSS のブレークポイントと同じ判定を JS 側でも行う。
 *
 * SSR とハイドレーション直後は false を返す。この初期値で表示がブレないのは
 * 「ページが setContent で注入したコンテンツ」に限る（注入自体がページ側の
 * useEffect で起きるため）。常時表示のデフォルト UI をこの hook で出し分けると
 * ハイドレーションまで空になるので、そこには使わないこと。
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const mql = window.matchMedia(query);
    setMatches(mql.matches);

    const onChange = (event: MediaQueryListEvent | MediaQueryList) =>
      setMatches(event.matches);

    // MediaQueryList が EventTarget を継承したのは Safari 14 / iOS 14 から。
    // 旧 WebView では addEventListener が無く、無条件に呼ぶと effect 内で
    // throw してアプリ全体がエラー画面になる。
    if (typeof mql.addEventListener === "function") {
      mql.addEventListener("change", onChange);
      return () => mql.removeEventListener("change", onChange);
    }
    mql.addListener(onChange);
    return () => mql.removeListener(onChange);
  }, [query]);

  return matches;
}

/**
 * Tailwind の `xl` (1280px) 以上。右カラムが表示される幅かどうか。
 *
 * 判定できない環境では false（= xl 未満）に倒れる。右カラムは xl 未満で
 * display:none なので、false 側に倒すと本文インラインに出る＝見える。
 * true 側に倒すと消えるため、安全側は false。
 */
export function useIsXlUp(): boolean {
  return useMediaQuery("(min-width: 1280px)");
}
