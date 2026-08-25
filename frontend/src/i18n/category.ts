import type { TFunction } from "i18next";

interface CategoryLike {
  name: string;
  slug?: string;
}

export function categoryName(cat: CategoryLike | null | undefined, t: TFunction): string {
  if (!cat) return "\u2014";
  if (cat.slug) {
    const key = `category.${cat.slug}`;
    if (t(key, { defaultValue: "" }) !== "") return t(key);
  }
  return cat.name;
}
