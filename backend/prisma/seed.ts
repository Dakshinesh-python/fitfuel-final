import { PrismaClient, Platform, MealType } from "@prisma/client";

const prisma = new PrismaClient();

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
}

const sampleMeals: SeedMeal[] = [
  { name: "Grilled Chicken Salad Bowl", restaurant: "FreshFit Kitchen", platform: "SWIGGY", cuisine: "Healthy Bowls", mealType: "LUNCH", calories: 420, proteinG: 38, carbsG: 30, fatG: 14, price: 220, isVegetarian: false, isVegan: false, allergens: [] },
  { name: "Paneer Tikka Bowl", restaurant: "Green Bowl Co", platform: "ZOMATO", cuisine: "North Indian", mealType: "LUNCH", calories: 450, proteinG: 28, carbsG: 40, fatG: 18, price: 190, isVegetarian: true, isVegan: false, allergens: ["dairy"] },
  { name: "Sprouts & Quinoa Salad", restaurant: "The Salad Bar", platform: "SWIGGY", cuisine: "Healthy Bowls", mealType: "LUNCH", calories: 320, proteinG: 18, carbsG: 45, fatG: 8, price: 180, isVegetarian: true, isVegan: true, allergens: [] },
  { name: "Egg White Omelette", restaurant: "Morning Fuel Cafe", platform: "ZOMATO", cuisine: "Continental", mealType: "BREAKFAST", calories: 250, proteinG: 24, carbsG: 6, fatG: 12, price: 150, isVegetarian: false, isVegan: false, allergens: ["egg"] },
  { name: "Masala Oats", restaurant: "Morning Fuel Cafe", platform: "ZOMATO", cuisine: "South Indian", mealType: "BREAKFAST", calories: 280, proteinG: 10, carbsG: 45, fatG: 6, price: 100, isVegetarian: true, isVegan: true, allergens: [] },
  { name: "Grilled Fish with Veggies", restaurant: "Coastal Grill", platform: "SWIGGY", cuisine: "Continental", mealType: "DINNER", calories: 480, proteinG: 40, carbsG: 20, fatG: 20, price: 320, isVegetarian: false, isVegan: false, allergens: ["fish"] },
  { name: "Tofu Stir Fry", restaurant: "Wok This Way", platform: "ZOMATO", cuisine: "Chinese", mealType: "DINNER", calories: 400, proteinG: 22, carbsG: 35, fatG: 16, price: 260, isVegetarian: true, isVegan: true, allergens: ["soy"] },
  { name: "Chicken Breast Wrap", restaurant: "Wrap It Up", platform: "SWIGGY", cuisine: "Continental", mealType: "LUNCH", calories: 460, proteinG: 34, carbsG: 42, fatG: 15, price: 210, isVegetarian: false, isVegan: false, allergens: ["gluten"] },
  { name: "Roasted Chana Chaat", restaurant: "Snack Shack", platform: "ZOMATO", cuisine: "North Indian", mealType: "SNACK", calories: 180, proteinG: 9, carbsG: 28, fatG: 4, price: 90, isVegetarian: true, isVegan: true, allergens: [] },
  { name: "Protein Smoothie", restaurant: "Blend Bar", platform: "SWIGGY", cuisine: "Healthy Bowls", mealType: "SNACK", calories: 220, proteinG: 20, carbsG: 25, fatG: 5, price: 140, isVegetarian: true, isVegan: false, allergens: ["dairy"] },
  { name: "Butter Chicken (Small)", restaurant: "Punjabi Dhaba", platform: "ZOMATO", cuisine: "North Indian", mealType: "DINNER", calories: 620, proteinG: 30, carbsG: 35, fatG: 38, price: 280, isVegetarian: false, isVegan: false, allergens: ["dairy"] },
  { name: "Idli Sambar (4 pcs)", restaurant: "Udupi Palace", platform: "SWIGGY", cuisine: "South Indian", mealType: "BREAKFAST", calories: 300, proteinG: 12, carbsG: 55, fatG: 4, price: 120, isVegetarian: true, isVegan: true, allergens: [] },
];

function healthScoreFor(m: (typeof sampleMeals)[number]): number {
  // Simple heuristic: reward high protein-to-calorie ratio, penalize high fat share
  const proteinRatio = (m.proteinG * 4) / m.calories;
  const fatRatio = (m.fatG * 9) / m.calories;
  const score = 100 * proteinRatio - 40 * fatRatio + 40;
  return Math.max(0, Math.min(100, Math.round(score)));
}

async function main() {
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
        deepLinkQuery: m.name,
      },
    });
  }

  console.log(`Seeded ${sampleMeals.length} meals across ${cuisines.length} cuisines.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
