"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

interface RightSidebarContextValue {
  content: ReactNode | null;
  setContent: (node: ReactNode | null) => void;
}

const RightSidebarContext = createContext<RightSidebarContextValue>({
  content: null,
  setContent: () => {},
});

export function RightSidebarProvider({ children }: { children: ReactNode }) {
  const [content, setContent] = useState<ReactNode | null>(null);
  return (
    <RightSidebarContext.Provider value={{ content, setContent }}>
      {children}
    </RightSidebarContext.Provider>
  );
}

export function useRightSidebar() {
  return useContext(RightSidebarContext);
}
