"use client";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
}

export function SearchBar({ value, onChange, onSearch }: SearchBarProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch();
  };

  return (
    <form onSubmit={handleSubmit} className="feed-filter-form">
      <input
        type="search"
        placeholder="搜索标题/摘要..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="feed-filter-search-input"
      />
      <button type="submit" className="feed-filter-submit">
        搜索
      </button>
    </form>
  );
}
