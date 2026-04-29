"use client";

const COLORS = [
  "#29736B", "#4D9E8C", "#8CC4B5", "#387063", "#2E6157",
  "#5A8F84", "#3D7A70", "#6BA89D", "#1F5C4F", "#438B7E",
];

function hashId(id: string): number {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

interface InitialAvatarProps {
  displayName: string;
  userId: string;
  size?: number;
  className?: string;
}

export function InitialAvatar({
  displayName,
  userId,
  size = 88,
  className = "",
}: InitialAvatarProps) {
  const initial = displayName.charAt(0).toUpperCase();
  const bg = COLORS[hashId(userId) % COLORS.length];

  return (
    <div
      className={`flex items-center justify-center rounded-full text-white font-bold ${className}`}
      style={{
        width: size,
        height: size,
        backgroundColor: bg,
        fontSize: size * 0.4,
      }}
      data-testid="initial-avatar"
    >
      {initial}
    </div>
  );
}
