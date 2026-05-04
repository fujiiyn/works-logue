"use client";

interface FilterChipOption {
  value: string;
  label: string;
  suffix?: string;
}

interface FilterChipGroupProps {
  options: FilterChipOption[];
  value: string;
  onChange: (value: string) => void;
  ariaLabel?: string;
}

export function FilterChipGroup({
  options,
  value,
  onChange,
  ariaLabel,
}: FilterChipGroupProps) {
  return (
    <div role="group" aria-label={ariaLabel} className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            data-testid={`filter-chip-${opt.value}`}
            onClick={() => onChange(opt.value)}
            className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
              active
                ? "border-primary bg-primary text-white"
                : "border-border bg-white text-primary-dark/80 hover:bg-bg-card"
            }`}
          >
            {opt.label}
            {opt.suffix ? (
              <span className="ml-1 text-xs opacity-70">{opt.suffix}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
