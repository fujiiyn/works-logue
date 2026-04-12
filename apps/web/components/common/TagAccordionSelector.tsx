"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronRight, ChevronDown, X } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface ApiTagTreeNode {
  id: string;
  name: string;
  category: string;
  is_leaf: boolean;
  children: ApiTagTreeNode[];
}

interface TagNode {
  id: string;
  name: string;
  category: string;
  parent_id: string | null;
}

interface TreeTagNode extends TagNode {
  children: TreeTagNode[];
}

function flattenTree(
  nodes: ApiTagTreeNode[],
  parentId: string | null = null,
): TagNode[] {
  const result: TagNode[] = [];
  for (const node of nodes) {
    result.push({ id: node.id, name: node.name, category: node.category, parent_id: parentId });
    if (node.children?.length) {
      result.push(...flattenTree(node.children, node.id));
    }
  }
  return result;
}

const LEFT_CATEGORIES = ["industry", "role", "skill"];
const RIGHT_CATEGORIES = ["occupation", "situation", "knowledge"];

const CATEGORY_LABELS: Record<string, string> = {
  industry: "業界",
  occupation: "職種",
  role: "役割",
  situation: "状況",
  skill: "スキル",
  knowledge: "ナレッジ",
};

interface TagAccordionSelectorProps {
  selectedTagIds: string[];
  onTagsChange: (ids: string[]) => void;
}

export function TagAccordionSelector({
  selectedTagIds,
  onTagsChange,
}: TagAccordionSelectorProps) {
  const [allTags, setAllTags] = useState<TagNode[]>([]);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiFetch<ApiTagTreeNode[]>("/api/v1/tags")
      .then((data) => {
        if (!cancelled) {
          setAllTags(flattenTree(data));
          setLoaded(true);
        }
      })
      .catch(() => { if (!cancelled) setLoaded(true); });
    return () => { cancelled = true; };
  }, []);

  const tagMap = useMemo(() => {
    const m = new Map<string, TagNode>();
    for (const t of allTags) m.set(t.id, t);
    return m;
  }, [allTags]);

  const getDescendantIds = useCallback(
    (nodeId: string, category: string): string[] => {
      const catTags = allTags.filter((t) => t.category === category);
      const childrenOf = (pid: string): string[] => {
        const kids = catTags.filter((t) => t.parent_id === pid);
        return kids.flatMap((k) => [k.id, ...childrenOf(k.id)]);
      };
      return childrenOf(nodeId);
    },
    [allTags],
  );

  const getLeafIds = useCallback(
    (nodeId: string, category: string): string[] => {
      const descendants = getDescendantIds(nodeId, category);
      if (descendants.length === 0) return [nodeId];
      const catTags = allTags.filter((t) => t.category === category);
      return descendants.filter((id) => !catTags.some((t) => t.parent_id === id));
    },
    [allTags, getDescendantIds],
  );

  const getCheckState = useCallback(
    (nodeId: string, category: string): "checked" | "unchecked" | "indeterminate" => {
      const leafIds = getLeafIds(nodeId, category);
      if (leafIds.length === 0) return selectedTagIds.includes(nodeId) ? "checked" : "unchecked";
      const checkedCount = leafIds.filter((id) => selectedTagIds.includes(id)).length;
      if (checkedCount === 0) return "unchecked";
      if (checkedCount === leafIds.length) return "checked";
      return "indeterminate";
    },
    [selectedTagIds, getLeafIds],
  );

  function toggleNode(nodeId: string, category: string) {
    const leafIds = getLeafIds(nodeId, category);
    const state = getCheckState(nodeId, category);
    if (state === "checked") {
      onTagsChange(selectedTagIds.filter((id) => !leafIds.includes(id)));
    } else {
      onTagsChange(Array.from(new Set([...selectedTagIds, ...leafIds])));
    }
  }

  function toggleCategory(cat: string) {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat); else next.add(cat);
      return next;
    });
  }

  function toggleExpand(nodeId: string) {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId); else next.add(nodeId);
      return next;
    });
  }

  function removeTag(tagId: string) {
    onTagsChange(selectedTagIds.filter((id) => id !== tagId));
  }

  const selectedTags = selectedTagIds
    .map((id) => tagMap.get(id))
    .filter(Boolean) as TagNode[];

  function buildTree(category: string): TreeTagNode[] {
    const catTags = allTags.filter((t) => t.category === category);
    const map = new Map<string, TreeTagNode>();
    for (const tag of catTags) map.set(tag.id, { ...tag, children: [] });
    const roots: TreeTagNode[] = [];
    for (const tag of catTags) {
      const node = map.get(tag.id)!;
      if (tag.parent_id && map.has(tag.parent_id)) {
        map.get(tag.parent_id)!.children.push(node);
      } else {
        roots.push(node);
      }
    }
    return roots;
  }

  function renderColumn(categories: string[]) {
    return (
      <div className="flex flex-1 flex-col gap-2">
        {categories.map((cat) => {
          const isOpen = expandedCategories.has(cat);
          const tree = buildTree(cat);
          return (
            <div
              key={cat}
              className="overflow-hidden rounded-md border border-border bg-bg-card"
            >
              <button
                type="button"
                onClick={() => toggleCategory(cat)}
                className="flex w-full items-center justify-between px-3.5 py-2.5 text-body-m font-medium text-primary-dark"
              >
                {CATEGORY_LABELS[cat]}
                <span className="text-[12px] text-text-secondary">
                  {isOpen ? "▾" : "▸"}
                </span>
              </button>
              {isOpen && (
                <>
                  <div className="h-px w-full bg-border" />
                  <div className="px-2.5 pb-2 pt-1.5">
                    {tree.map((node) => (
                      <TreeNode
                        key={node.id}
                        node={node}
                        depth={0}
                        category={cat}
                        expandedNodes={expandedNodes}
                        toggleExpand={toggleExpand}
                        getCheckState={getCheckState}
                        toggleNode={toggleNode}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  if (!loaded) return null;

  return (
    <div data-testid="tag-accordion-selector">
      {/* Selected chips */}
      {selectedTags.length > 0 && (
        <div className="mb-2.5 flex flex-wrap gap-1.5" data-testid="tag-selector-chips">
          {selectedTags.map((tag) => (
            <span
              key={tag.id}
              className="flex items-center gap-1 rounded-sm bg-primary-light-bg px-2 py-1 text-[11px] text-primary"
            >
              {tag.name}
              <button
                type="button"
                onClick={() => removeTag(tag.id)}
                className="ml-0.5"
                aria-label={`${tag.name}を削除`}
              >
                <X size={12} strokeWidth={1.5} />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Two-column accordions */}
      <div className="flex gap-2">
        {renderColumn(LEFT_CATEGORIES)}
        {renderColumn(RIGHT_CATEGORIES)}
      </div>
    </div>
  );
}

function TreeNode({
  node,
  depth,
  category,
  expandedNodes,
  toggleExpand,
  getCheckState,
  toggleNode,
}: {
  node: TreeTagNode;
  depth: number;
  category: string;
  expandedNodes: Set<string>;
  toggleExpand: (id: string) => void;
  getCheckState: (id: string, cat: string) => "checked" | "unchecked" | "indeterminate";
  toggleNode: (id: string, cat: string) => void;
}) {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedNodes.has(node.id);
  const checkState = getCheckState(node.id, category);

  const paddingLeft =
    depth === 0 ? "pl-1" : depth === 1 ? "pl-[22px]" : "pl-[40px]";

  return (
    <div>
      <div className={`flex items-center gap-1.5 py-[3px] ${paddingLeft}`}>
        {hasChildren ? (
          <button
            type="button"
            onClick={() => toggleExpand(node.id)}
            className="flex h-3 w-3 items-center justify-center text-text-secondary"
            aria-label={isExpanded ? "折りたたむ" : "展開する"}
          >
            {isExpanded ? (
              <ChevronDown size={12} strokeWidth={1.5} />
            ) : (
              <ChevronRight size={12} strokeWidth={1.5} />
            )}
          </button>
        ) : (
          <span className="h-3 w-3" />
        )}

        <button
          type="button"
          onClick={() => toggleNode(node.id, category)}
          className={`flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-[3px] border-[1.5px] transition-colors ${
            checkState === "unchecked"
              ? "border-border bg-white"
              : "border-primary bg-primary"
          }`}
          aria-label={node.name}
        >
          {checkState === "checked" && (
            <svg width="9" height="7" viewBox="0 0 10 8" fill="none">
              <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
          {checkState === "indeterminate" && (
            <svg width="8" height="2" viewBox="0 0 8 2" fill="none">
              <path d="M1 1H7" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          )}
        </button>

        <span
          className="cursor-pointer select-none text-[12px] text-primary-dark"
          onClick={() => toggleNode(node.id, category)}
        >
          {node.name}
        </span>
      </div>

      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              category={category}
              expandedNodes={expandedNodes}
              toggleExpand={toggleExpand}
              getCheckState={getCheckState}
              toggleNode={toggleNode}
            />
          ))}
        </div>
      )}
    </div>
  );
}
