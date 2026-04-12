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
  children?: TagNode[];
}

/** Flatten the nested tree response from API into a flat array with parent_id */
function flattenTree(
  nodes: ApiTagTreeNode[],
  parentId: string | null = null,
): TagNode[] {
  const result: TagNode[] = [];
  for (const node of nodes) {
    result.push({
      id: node.id,
      name: node.name,
      category: node.category,
      parent_id: parentId,
    });
    if (node.children && node.children.length > 0) {
      result.push(...flattenTree(node.children, node.id));
    }
  }
  return result;
}

interface TagSelectorProps {
  selectedTagIds: string[];
  onTagsChange: (ids: string[]) => void;
  categories?: string[];
}

const DEFAULT_CATEGORIES = [
  "industry",
  "occupation",
  "role",
  "situation",
  "skill",
  "knowledge",
];

const CATEGORY_LABELS: Record<string, string> = {
  industry: "業界",
  occupation: "職種",
  role: "役割",
  situation: "状況",
  skill: "スキル",
  knowledge: "ナレッジ",
};

export function TagSelector({
  selectedTagIds,
  onTagsChange,
  categories = DEFAULT_CATEGORIES,
}: TagSelectorProps) {
  const [activeCategory, setActiveCategory] = useState(categories[0]);
  const [allTags, setAllTags] = useState<TagNode[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [loaded, setLoaded] = useState(false);

  // Fetch tags
  useEffect(() => {
    let cancelled = false;
    apiFetch<ApiTagTreeNode[]>("/api/v1/tags")
      .then((data) => {
        if (!cancelled) {
          setAllTags(flattenTree(data));
          setLoaded(true);
        }
      })
      .catch(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Build tree for active category
  const tree = useMemo(() => {
    const categoryTags = allTags.filter((t) => t.category === activeCategory);
    const map = new Map<string, TagNode & { children: TagNode[] }>();

    for (const tag of categoryTags) {
      map.set(tag.id, { ...tag, children: [] });
    }

    const roots: TagNode[] = [];
    for (const tag of categoryTags) {
      const node = map.get(tag.id)!;
      if (tag.parent_id && map.has(tag.parent_id)) {
        map.get(tag.parent_id)!.children.push(node);
      } else {
        roots.push(node);
      }
    }

    return roots;
  }, [allTags, activeCategory]);

  // Flat lookup map for all tags
  const tagMap = useMemo(() => {
    const m = new Map<string, TagNode>();
    for (const t of allTags) m.set(t.id, t);
    return m;
  }, [allTags]);

  // Get all descendant IDs
  const getDescendantIds = useCallback(
    (nodeId: string): string[] => {
      const categoryTags = allTags.filter((t) => t.category === activeCategory);
      const childrenOf = (pid: string): string[] => {
        const kids = categoryTags.filter((t) => t.parent_id === pid);
        return kids.flatMap((k) => [k.id, ...childrenOf(k.id)]);
      };
      return childrenOf(nodeId);
    },
    [allTags, activeCategory],
  );

  // Get leaf IDs under a node (including itself if it's a leaf)
  const getLeafIds = useCallback(
    (nodeId: string): string[] => {
      const descendants = getDescendantIds(nodeId);
      if (descendants.length === 0) return [nodeId];
      const categoryTags = allTags.filter((t) => t.category === activeCategory);
      return descendants.filter(
        (id) => !categoryTags.some((t) => t.parent_id === id),
      );
    },
    [allTags, activeCategory, getDescendantIds],
  );

  // Check state for a node
  const getCheckState = useCallback(
    (nodeId: string): "checked" | "unchecked" | "indeterminate" => {
      const leafIds = getLeafIds(nodeId);
      if (leafIds.length === 0) {
        return selectedTagIds.includes(nodeId) ? "checked" : "unchecked";
      }
      const checkedCount = leafIds.filter((id) =>
        selectedTagIds.includes(id),
      ).length;
      if (checkedCount === 0) return "unchecked";
      if (checkedCount === leafIds.length) return "checked";
      return "indeterminate";
    },
    [selectedTagIds, getLeafIds],
  );

  function toggleNode(nodeId: string) {
    const leafIds = getLeafIds(nodeId);
    const state = getCheckState(nodeId);

    if (state === "checked") {
      // Uncheck all leaves
      onTagsChange(selectedTagIds.filter((id) => !leafIds.includes(id)));
    } else {
      // Check all leaves
      const newIds = new Set([...selectedTagIds, ...leafIds]);
      onTagsChange(Array.from(newIds));
    }
  }

  function toggleExpand(nodeId: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  }

  function removeTag(tagId: string) {
    onTagsChange(selectedTagIds.filter((id) => id !== tagId));
  }

  // Selected chips (from all categories)
  const selectedTags = selectedTagIds
    .map((id) => tagMap.get(id))
    .filter(Boolean) as TagNode[];

  return (
    <div data-testid="tag-selector">
      {/* Selected chips */}
      {selectedTags.length > 0 && (
        <div className="mb-3">
          <p className="mb-2 text-[11px] font-medium text-text-secondary">選択中</p>
        <div className="flex flex-wrap gap-1.5" data-testid="tag-selector-chips">
          {selectedTags.map((tag) => (
            <span
              key={tag.id}
              className="flex items-center gap-1 rounded-sm bg-primary-light-bg px-[8px] py-[4px] text-caption text-primary"
            >
              {tag.name}
              <button
                onClick={() => removeTag(tag.id)}
                className="ml-0.5"
                data-testid={`tag-chip-remove-${tag.id}`}
                aria-label={`${tag.name}を削除`}
              >
                <X size={12} strokeWidth={1.5} />
              </button>
            </span>
          ))}
        </div>
        </div>
      )}

      {/* Category tabs */}
      <div className="mb-3 flex flex-wrap gap-1" data-testid="tag-selector-tabs">
        {categories.map((cat) => {
          const isActive = cat === activeCategory;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`rounded-sm px-[10px] py-[4px] text-caption transition-colors ${
                isActive
                  ? "bg-primary text-white"
                  : "text-text-secondary hover:bg-primary-light-bg/30"
              }`}
              data-testid={`tag-selector-tab-${cat}`}
            >
              {CATEGORY_LABELS[cat] ?? cat}
            </button>
          );
        })}
      </div>

      {/* Tree */}
      {loaded && (
        <div className="max-h-[360px] overflow-y-auto" data-testid="tag-selector-tree">
          {tree.length === 0 ? (
            <p className="py-4 text-center text-body-s text-text-muted">
              タグがありません
            </p>
          ) : (
            tree.map((node) => (
              <TreeNode
                key={node.id}
                node={node}
                depth={0}
                expanded={expanded}
                toggleExpand={toggleExpand}
                getCheckState={getCheckState}
                toggleNode={toggleNode}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

function TreeNode({
  node,
  depth,
  expanded,
  toggleExpand,
  getCheckState,
  toggleNode,
}: {
  node: TagNode & { children?: TagNode[] };
  depth: number;
  expanded: Set<string>;
  toggleExpand: (id: string) => void;
  getCheckState: (id: string) => "checked" | "unchecked" | "indeterminate";
  toggleNode: (id: string) => void;
}) {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expanded.has(node.id);
  const checkState = getCheckState(node.id);

  const paddingLeft =
    depth === 0 ? "pl-[4px]" : depth === 1 ? "pl-[22px]" : "pl-[40px]";

  return (
    <div>
      <div
        className={`flex items-center gap-1.5 py-[3px] ${paddingLeft}`}
        data-testid={`tag-node-${node.id}`}
      >
        {/* Expand/collapse chevron */}
        {hasChildren ? (
          <button
            onClick={() => toggleExpand(node.id)}
            className="flex h-4 w-4 items-center justify-center text-text-muted"
            data-testid={`tag-expand-${node.id}`}
            aria-label={isExpanded ? "折りたたむ" : "展開する"}
          >
            {isExpanded ? (
              <ChevronDown size={14} strokeWidth={1.5} />
            ) : (
              <ChevronRight size={14} strokeWidth={1.5} />
            )}
          </button>
        ) : (
          <span className="h-4 w-4" />
        )}

        {/* Checkbox */}
        <button
          onClick={() => toggleNode(node.id)}
          className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-[2px] border transition-colors ${
            checkState === "unchecked"
              ? "border-border bg-white"
              : "border-primary bg-primary"
          }`}
          data-testid={`tag-checkbox-${node.id}`}
          aria-label={node.name}
        >
          {checkState === "checked" && (
            <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
              <path
                d="M1 4L3.5 6.5L9 1"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
          {checkState === "indeterminate" && (
            <svg width="8" height="2" viewBox="0 0 8 2" fill="none">
              <path
                d="M1 1H7"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          )}
        </button>

        {/* Label */}
        <span
          className="cursor-pointer select-none text-body-s text-primary-dark"
          onClick={() => toggleNode(node.id)}
        >
          {node.name}
        </span>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child as TagNode & { children?: TagNode[] }}
              depth={depth + 1}
              expanded={expanded}
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
