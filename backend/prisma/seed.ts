import { PrismaClient, Platform, MealType } from "@prisma/client";

const prisma = new PrismaClient();

/**
 * Unsplash CDN URLs matched to each meal's cuisine/type.
 * All photo IDs have been selected from Unsplash's public catalog.
 * Format: https://images.unsplash.com/photo-<id>?auto=format&fit=crop&w=600&q=80
 *
 * IMPORTANT: Any meal without a non-empty imageUrl will cause the seed to fail
 * loudly (see validation below). Never ship the seed with a null/empty imageUrl.
 */

interface SeedMeal {
  name: string;
  restaurant: string;
  platform: Platform;
  cuisine: string;
  mealType: MealType;
  calories: number;
  proteinG: number;
  carbsG: number;
  fatG: number;
  price: number;
  isVegetarian: boolean;
  isVegan: boolean;
  allergens: string[];
  imageUrl: string; // required — seed fails loudly if empty
}

const sampleMeals: SeedMeal[] = [
  {
    name: "Grilled Chicken Salad Bowl",
    restaurant: "FreshFit Kitchen",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "LUNCH",
    calories: 420, proteinG: 38, carbsG: 30, fatG: 14, price: 220,
    isVegetarian: false, isVegan: false, allergens: [],
    // Grilled chicken salad bowl — bright colourful bowl with greens & protein
    imageUrl: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Paneer Tikka Bowl",
    restaurant: "Green Bowl Co",
    platform: "ZOMATO",
    cuisine: "North Indian",
    mealType: "LUNCH",
    calories: 450, proteinG: 28, carbsG: 40, fatG: 18, price: 190,
    isVegetarian: true, isVegan: false, allergens: ["dairy"],
    // Paneer / Indian curry — rich orange masala dish
    imageUrl: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Sprouts & Quinoa Salad",
    restaurant: "The Salad Bar",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "LUNCH",
    calories: 320, proteinG: 18, carbsG: 45, fatG: 8, price: 180,
    isVegetarian: true, isVegan: true, allergens: [],
    // Quinoa + sprouts salad bowl with colourful vegetables
    imageUrl: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Egg White Omelette",
    restaurant: "Morning Fuel Cafe",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "BREAKFAST",
    calories: 250, proteinG: 24, carbsG: 6, fatG: 12, price: 150,
    isVegetarian: false, isVegan: false, allergens: ["egg"],
    // Classic folded omelette on a plate
    imageUrl: "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Masala Oats",
    restaurant: "Morning Fuel Cafe",
    platform: "ZOMATO",
    cuisine: "South Indian",
    mealType: "BREAKFAST",
    calories: 280, proteinG: 10, carbsG: 45, fatG: 6, price: 100,
    isVegetarian: true, isVegan: true, allergens: [],
    // Oats / porridge bowl with toppings
    imageUrl: "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Grilled Fish with Veggies",
    restaurant: "Coastal Grill",
    platform: "SWIGGY",
    cuisine: "Continental",
    mealType: "DINNER",
    calories: 480, proteinG: 40, carbsG: 20, fatG: 20, price: 320,
    isVegetarian: false, isVegan: false, allergens: ["fish"],
    // Grilled fish fillet with roasted vegetables
    imageUrl: "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Tofu Stir Fry",
    restaurant: "Wok This Way",
    platform: "ZOMATO",
    cuisine: "Chinese",
    mealType: "DINNER",
    calories: 400, proteinG: 22, carbsG: 35, fatG: 16, price: 260,
    isVegetarian: true, isVegan: true, allergens: ["soy"],
    // Asian stir fry with tofu, vegetables, noodles
    imageUrl: "https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Chicken Breast Wrap",
    restaurant: "Wrap It Up",
    platform: "SWIGGY",
    cuisine: "Continental",
    mealType: "LUNCH",
    calories: 460, proteinG: 34, carbsG: 42, fatG: 15, price: 210,
    isVegetarian: false, isVegan: false, allergens: ["gluten"],
    // Grilled chicken wrap / burrito style
    imageUrl: "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Roasted Chana Chaat",
    restaurant: "Snack Shack",
    platform: "ZOMATO",
    cuisine: "North Indian",
    mealType: "SNACK",
    calories: 180, proteinG: 9, carbsG: 28, fatG: 4, price: 90,
    isVegetarian: true, isVegan: true, allergens: [],
    // Chickpea / chana chaat bowl with chutneys
    imageUrl: "https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Protein Smoothie",
    restaurant: "Blend Bar",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "SNACK",
    calories: 220, proteinG: 20, carbsG: 25, fatG: 5, price: 140,
    isVegetarian: true, isVegan: false, allergens: ["dairy"],
    // Colourful protein smoothie / shake in glass
    imageUrl: "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Butter Chicken (Small)",
    restaurant: "Punjabi Dhaba",
    platform: "ZOMATO",
    cuisine: "North Indian",
    mealType: "DINNER",
    calories: 620, proteinG: 30, carbsG: 35, fatG: 38, price: 280,
    isVegetarian: false, isVegan: false, allergens: ["dairy"],
    // Butter chicken / murgh makhani — creamy orange curry
    imageUrl: "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Idli Sambar (4 pcs)",
    restaurant: "Udupi Palace",
    platform: "SWIGGY",
    cuisine: "South Indian",
    mealType: "BREAKFAST",
    calories: 300, proteinG: 12, carbsG: 55, fatG: 4, price: 120,
    isVegetarian: true, isVegan: true, allergens: [],
    // Idli with sambar and chutneys on a banana leaf / plate
    imageUrl: "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Peanut Satay Chicken Skewers",
    restaurant: "Wok This Way",
    platform: "ZOMATO",
    cuisine: "Chinese",
    mealType: "DINNER",
    calories: 440, proteinG: 32, carbsG: 22, fatG: 24, price: 240,
    isVegetarian: false, isVegan: false, allergens: ["peanuts"],
    // Grilled chicken skewers / satay with peanut sauce
    imageUrl: "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Almond Granola Bowl",
    restaurant: "Blend Bar",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "BREAKFAST",
    calories: 340, proteinG: 14, carbsG: 40, fatG: 15, price: 160,
    isVegetarian: true, isVegan: false, allergens: ["nuts", "dairy"],
    // Granola bowl with yogurt, berries, and nuts
    imageUrl: "https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38?auto=format&fit=crop&w=600&q=80",
  },
];

function healthScoreFor(m: (typeof sampleMeals)[number]): number {
  // Simple heuristic: reward high protein-to-calorie ratio, penalize high fat share
  const proteinRatio = (m.proteinG * 4) / m.calories;
  const fatRatio = (m.fatG * 9) / m.calories;
  const score = 100 * proteinRatio - 40 * fatRatio + 40;
  return Math.max(0, Math.min(100, Math.round(score)));
}

/**
 * Guard: fail loudly if any meal is missing imageUrl.
 * This prevents a broken seed from silently shipping meals without photos.
 */
function validateImageUrls(meals: SeedMeal[]): void {
  const missing = meals
    .filter((m) => !m.imageUrl || m.imageUrl.trim() === "")
    .map((m) => m.name);

  if (missing.length > 0) {
    throw new Error(
      `[seed] ABORTED — the following meals are missing imageUrl:\n` +
        missing.map((n) => `  • ${n}`).join("\n") +
        `\nAdd a valid Unsplash URL for each meal before re-running the seed.`
    );
  }
}

async function main() {
  // Validate images before touching the database
  validateImageUrls(sampleMeals);

  console.log("Seeding meals...");
  await prisma.meal.deleteMany();

  for (const m of sampleMeals) {
    await prisma.meal.create({
      data: {
        name: m.name,
        restaurant: m.restaurant,
        platform: m.platform,
        cuisine: m.cuisine,
        mealType: m.mealType,
        calories: m.calories,
        proteinG: m.proteinG,
        carbsG: m.carbsG,
        fatG: m.fatG,
        price: m.price,
        healthScore: healthScoreFor(m),
        isVegetarian: m.isVegetarian,
        isVegan: m.isVegan,
        allergens: m.allergens,
        imageUrl: m.imageUrl,
        deepLinkQuery: m.name,
      },
    });
  }

  const uniqueCuisines = new Set(sampleMeals.map((m) => m.cuisine));
  console.log(`Seeded ${sampleMeals.length} meals across ${uniqueCuisines.size} cuisines.`);
  console.log("All meals have imageUrl ✓");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
