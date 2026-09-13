"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useIsXlUp } from "@/hooks/use-media-query";

/**
 * xl 未満では右カラムが存在しないため、注入されたコンテンツを本文のどこに
 * インライン展開するかをページ側が指定する。
 * - "top": 本文の先頭（開花スコアなど、記事より先に見せたいもの）
 * - "bottom": 本文の末尾（貢献者リスト・バッジなど、読了後の補足）
 * - "none": モバイルでは出さない（本文側に同等の UI が既にある場合）
 */
export type RightSidebarPlacement = "top" | "bottom" | "none";

/** インラインスロットとして実在する配置（"none" はスロットを持たない） */
export type RightSidebarSlot = Exclude<RightSidebarPlacement, "none">;

/** content を実際にどこへ描画するか。null は注入コンテンツなし */
export type RightSidebarTarget = "aside" | RightSidebarPlacement | null;

/**
 * 注入時は placement の指定を必須にする（省略できると、モバイルでの見え方を
 * 考えないまま既定値に落ちたのか意図的なのか区別がつかない）。
 * クリア時の `setContent(null)` は引数1つで呼べる。
 */
export type SetRightSidebarContent = {
  (node: null): void;
  (node: ReactNode, placement: RightSidebarPlacement): void;
};

interface RightSidebarContextValue {
  content: ReactNode | null;
  target: RightSidebarTarget;
  setContent: SetRightSidebarContent;
}

const RightSidebarContext = createContext<RightSidebarContextValue | null>(null);

export function RightSidebarProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{
    content: ReactNode | null;
    placement: RightSidebarPlacement;
  }>({ content: null, placement: "bottom" });

  // ページ側の useEffect 依存配列に入るため参照を固定する
  const setContent = useCallback(
    (node: ReactNode | null, placement: RightSidebarPlacement = "bottom") => {
      setState({ content: node ?? null, placement });
    },
    [],
  ) as SetRightSidebarContent;

  // 幅判定はここ1か所だけ。右カラムとインラインが別々に matchMedia を持つと、
  // 両方が true の瞬間に二重マウントしうる。
  const isXlUp = useIsXlUp();
  const target: RightSidebarTarget =
    state.content == null ? null : isXlUp ? "aside" : state.placement;

  const value = useMemo(
    () => ({ content: state.content, target, setContent }),
    [state.content, target, setContent],
  );

  return (
    <RightSidebarContext.Provider value={value}>
      {children}
    </RightSidebarContext.Provider>
  );
}

export function useRightSidebar() {
  const ctx = useContext(RightSidebarContext);
  if (!ctx) {
    throw new Error(
      "useRightSidebar は <RightSidebarProvider>（app/layout.tsx）の内側で使うこと。" +
        "外側から setContent を呼んでも内容は黙って捨てられる。",
    );
  }
  return ctx;
}
