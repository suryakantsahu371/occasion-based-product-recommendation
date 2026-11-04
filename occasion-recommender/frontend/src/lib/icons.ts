import {
  Baby,
  Briefcase,
  Cake,
  Flame,
  Flower2,
  Gem,
  Gift,
  Heart,
  HeartHandshake,
  HandHeart,
  Home,
  PartyPopper,
  Palette,
  Sparkles,
  Stethoscope,
  TreePine,
  type LucideIcon,
} from "lucide-react";

/** Icon names sent by ``GET /api/occasions`` -> lucide components (explicit imports keep the bundle small). */
const ICONS: Record<string, LucideIcon> = {
  Baby,
  Briefcase,
  Cake,
  Flame,
  Flower2,
  Gem,
  Gift,
  Heart,
  HeartHandshake,
  HandHeart,
  Home,
  PartyPopper,
  Palette,
  Sparkles,
  Stethoscope,
  TreePine,
};

export const iconFor = (name: string): LucideIcon => ICONS[name] ?? Gift;

/** Quick-pick chips shown under the search bar: the text is sent as the query. */
export const QUICK_PICKS: { label: string; icon: LucideIcon }[] = [
  { label: "Birthday", icon: Cake },
  { label: "Wedding", icon: Heart },
  { label: "Diwali", icon: Flame },
  { label: "Valentine's Day", icon: HeartHandshake },
  { label: "Office Party", icon: Briefcase },
  { label: "Housewarming", icon: Home },
];
