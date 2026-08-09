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
  imageUrl: string; // required — seed fails loudly if empty
}

/**
 * 65 meals across BREAKFAST, LUNCH, DINNER, SNACK.
 * Covers vegetarian, vegan, non-veg, high-protein, low-carb,
 * and multiple cuisines (North Indian, South Indian, Continental,
 * Mediterranean, Healthy Bowls, Chinese, Middle Eastern, Japanese).
 * All images are public Unsplash CDN URLs.
 */
const sampleMeals: SeedMeal[] = [

  // ─── BREAKFAST ─────────────────────────────────────────────────────────────

  {
    name: "Egg White Omelette",
    restaurant: "Morning Fuel Cafe",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "BREAKFAST",
    calories: 250, proteinG: 24, carbsG: 6, fatG: 12, price: 150,
    isVegetarian: false, isVegan: false, allergens: ["egg"],
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
    imageUrl: "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Almond Granola Bowl",
    restaurant: "Blend Bar",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "BREAKFAST",
    calories: 340, proteinG: 14, carbsG: 40, fatG: 15, price: 160,
    isVegetarian: true, isVegan: false, allergens: ["nuts", "dairy"],
    imageUrl: "https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Idli Sambar (4 pcs)",
    restaurant: "Udupi Palace",
    platform: "SWIGGY",
    cuisine: "South Indian",
    mealType: "BREAKFAST",
    calories: 300, proteinG: 12, carbsG: 55, fatG: 4, price: 120,
    isVegetarian: true, isVegan: true, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Greek Yogurt Parfait",
    restaurant: "FreshFit Kitchen",
    platform: "SWIGGY",
    cuisine: "Continental",
    mealType: "BREAKFAST",
    calories: 290, proteinG: 18, carbsG: 36, fatG: 6, price: 180,
    isVegetarian: true, isVegan: false, allergens: ["dairy"],
    imageUrl: "https://images.unsplash.com/photo-1571748982800-fa51082c2224?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Banana Peanut Butter Toast",
    restaurant: "Cafe Green",
    platform: "ZOMATO",
    cuisine: "Healthy Bowls",
    mealType: "BREAKFAST",
    calories: 360, proteinG: 12, carbsG: 52, fatG: 11, price: 130,
    isVegetarian: true, isVegan: true, allergens: ["gluten", "peanuts"],
    imageUrl: "https://images.unsplash.com/photo-1619546813926-a78fa6372cd2?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Moong Dal Chilla",
    restaurant: "The Protein Kitchen",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "BREAKFAST",
    calories: 310, proteinG: 16, carbsG: 42, fatG: 7, price: 140,
    isVegetarian: true, isVegan: true, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1505253758473-96b7015fcd40?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Overnight Chia Pudding",
    restaurant: "Blend Bar",
    platform: "ZOMATO",
    cuisine: "Healthy Bowls",
    mealType: "BREAKFAST",
    calories: 260, proteinG: 9, carbsG: 32, fatG: 10, price: 170,
    isVegetarian: true, isVegan: true, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1574570068036-5773d5fe4a44?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Scrambled Eggs with Avocado",
    restaurant: "Morning Fuel Cafe",
    platform: "SWIGGY",
    cuisine: "Continental",
    mealType: "BREAKFAST",
    calories: 390, proteinG: 22, carbsG: 14, fatG: 26, price: 220,
    isVegetarian: false, isVegan: false, allergens: ["egg"],
    imageUrl: "https://images.unsplash.com/photo-1510693206972-df098062cb71?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Poha with Peanuts",
    restaurant: "Udupi Palace",
    platform: "ZOMATO",
    cuisine: "South Indian",
    mealType: "BREAKFAST",
    calories: 270, proteinG: 8, carbsG: 48, fatG: 6, price: 90,
    isVegetarian: true, isVegan: true, allergens: ["peanuts"],
    imageUrl: "https://images.unsplash.com/photo-1606491955791-11c5c25db1b2?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "High-Protein Paneer Bhurji",
    restaurant: "The Protein Kitchen",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "BREAKFAST",
    calories: 380, proteinG: 26, carbsG: 12, fatG: 24, price: 200,
    isVegetarian: true, isVegan: false, allergens: ["dairy"],
    imageUrl: "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Avocado Toast with Poached Egg",
    restaurant: "FreshFit Kitchen",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "BREAKFAST",
    calories: 410, proteinG: 18, carbsG: 32, fatG: 24, price: 240,
    isVegetarian: false, isVegan: false, allergens: ["egg", "gluten"],
    imageUrl: "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?auto=format&fit=crop&w=600&q=80",
  },

  // ─── LUNCH ─────────────────────────────────────────────────────────────────

  {
    name: "Grilled Chicken Salad Bowl",
    restaurant: "FreshFit Kitchen",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "LUNCH",
    calories: 420, proteinG: 38, carbsG: 30, fatG: 14, price: 220,
    isVegetarian: false, isVegan: false, allergens: [],
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
    imageUrl: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Chicken Breast Wrap",
    restaurant: "Wrap It Up",
    platform: "SWIGGY",
    cuisine: "Continental",
    mealType: "LUNCH",
    calories: 460, proteinG: 34, carbsG: 42, fatG: 15, price: 210,
    isVegetarian: false, isVegan: false, allergens: ["gluten"],
    imageUrl: "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Mediterranean Falafel Bowl",
    restaurant: "The Salad Bar",
    platform: "ZOMATO",
    cuisine: "Mediterranean",
    mealType: "LUNCH",
    calories: 480, proteinG: 20, carbsG: 58, fatG: 16, price: 240,
    isVegetarian: true, isVegan: true, allergens: ["gluten", "sesame"],
    imageUrl: "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Tuna Nicoise Salad",
    restaurant: "Coastal Grill",
    platform: "SWIGGY",
    cuisine: "Continental",
    mealType: "LUNCH",
    calories: 390, proteinG: 36, carbsG: 24, fatG: 16, price: 300,
    isVegetarian: false, isVegan: false, allergens: ["fish", "egg"],
    imageUrl: "https://images.unsplash.com/photo-1580013759032-c96505e24c1f?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Dal Makhani with Brown Rice",
    restaurant: "Punjabi Dhaba",
    platform: "ZOMATO",
    cuisine: "North Indian",
    mealType: "LUNCH",
    calories: 510, proteinG: 22, carbsG: 70, fatG: 14, price: 180,
    isVegetarian: true, isVegan: false, allergens: ["dairy"],
    imageUrl: "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Soba Noodle Veggie Bowl",
    restaurant: "Wok This Way",
    platform: "SWIGGY",
    cuisine: "Japanese",
    mealType: "LUNCH",
    calories: 370, proteinG: 14, carbsG: 60, fatG: 8, price: 260,
    isVegetarian: true, isVegan: true, allergens: ["gluten", "soy"],
    imageUrl: "https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Chicken & Lentil Soup",
    restaurant: "FreshFit Kitchen",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "LUNCH",
    calories: 340, proteinG: 32, carbsG: 30, fatG: 8, price: 200,
    isVegetarian: false, isVegan: false, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Rajma Bowl with Brown Rice",
    restaurant: "Green Bowl Co",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "LUNCH",
    calories: 490, proteinG: 20, carbsG: 72, fatG: 8, price: 160,
    isVegetarian: true, isVegan: true, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Grilled Salmon Salad",
    restaurant: "Coastal Grill",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "LUNCH",
    calories: 440, proteinG: 40, carbsG: 18, fatG: 22, price: 380,
    isVegetarian: false, isVegan: false, allergens: ["fish"],
    imageUrl: "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Palak Tofu Curry",
    restaurant: "Green Bowl Co",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "LUNCH",
    calories: 380, proteinG: 22, carbsG: 30, fatG: 18, price: 200,
    isVegetarian: true, isVegan: true, allergens: ["soy"],
    imageUrl: "https://images.unsplash.com/photo-1546833998-877b37c2e5c6?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Egg Salad Sandwich (Whole Wheat)",
    restaurant: "Cafe Green",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "LUNCH",
    calories: 400, proteinG: 20, carbsG: 44, fatG: 16, price: 160,
    isVegetarian: false, isVegan: false, allergens: ["egg", "gluten"],
    imageUrl: "https://images.unsplash.com/photo-1484723091739-30a097e8f929?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Hummus & Pita with Veggie Sticks",
    restaurant: "The Salad Bar",
    platform: "SWIGGY",
    cuisine: "Mediterranean",
    mealType: "LUNCH",
    calories: 360, proteinG: 12, carbsG: 50, fatG: 12, price: 200,
    isVegetarian: true, isVegan: true, allergens: ["gluten", "sesame"],
    imageUrl: "https://images.unsplash.com/photo-1542014740373-51ad6425a7e6?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Turkey Quinoa Power Bowl",
    restaurant: "FreshFit Kitchen",
    platform: "ZOMATO",
    cuisine: "Healthy Bowls",
    mealType: "LUNCH",
    calories: 470, proteinG: 42, carbsG: 38, fatG: 14, price: 320,
    isVegetarian: false, isVegan: false, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
  },

  // ─── DINNER ─────────────────────────────────────────────────────────────────

  {
    name: "Grilled Fish with Veggies",
    restaurant: "Coastal Grill",
    platform: "SWIGGY",
    cuisine: "Continental",
    mealType: "DINNER",
    calories: 480, proteinG: 40, carbsG: 20, fatG: 20, price: 320,
    isVegetarian: false, isVegan: false, allergens: ["fish"],
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
    imageUrl: "https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Peanut Satay Chicken Skewers",
    restaurant: "Wok This Way",
    platform: "ZOMATO",
    cuisine: "Chinese",
    mealType: "DINNER",
    calories: 440, proteinG: 32, carbsG: 22, fatG: 24, price: 240,
    isVegetarian: false, isVegan: false, allergens: ["peanuts"],
    imageUrl: "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Butter Chicken (Small)",
    restaurant: "Punjabi Dhaba",
    platform: "ZOMATO",
    cuisine: "North Indian",
    mealType: "DINNER",
    calories: 520, proteinG: 30, carbsG: 30, fatG: 28, price: 280,
    isVegetarian: false, isVegan: false, allergens: ["dairy"],
    imageUrl: "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Baked Lemon Herb Chicken",
    restaurant: "FreshFit Kitchen",
    platform: "SWIGGY",
    cuisine: "Continental",
    mealType: "DINNER",
    calories: 450, proteinG: 44, carbsG: 12, fatG: 22, price: 340,
    isVegetarian: false, isVegan: false, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Mushroom & Spinach Pasta (Whole Wheat)",
    restaurant: "Cafe Green",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "DINNER",
    calories: 490, proteinG: 18, carbsG: 68, fatG: 14, price: 260,
    isVegetarian: true, isVegan: false, allergens: ["gluten", "dairy"],
    imageUrl: "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Chicken Tikka Masala (Light)",
    restaurant: "Punjabi Dhaba",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "DINNER",
    calories: 480, proteinG: 36, carbsG: 28, fatG: 22, price: 290,
    isVegetarian: false, isVegan: false, allergens: ["dairy"],
    imageUrl: "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Grilled Prawn Platter",
    restaurant: "Coastal Grill",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "DINNER",
    calories: 380, proteinG: 42, carbsG: 8, fatG: 18, price: 420,
    isVegetarian: false, isVegan: false, allergens: ["shellfish"],
    imageUrl: "https://images.unsplash.com/photo-1603360946369-dc9bb6258143?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Vegetable Dal with Millet Roti",
    restaurant: "Green Bowl Co",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "DINNER",
    calories: 430, proteinG: 18, carbsG: 62, fatG: 10, price: 150,
    isVegetarian: true, isVegan: true, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1546833998-877b37c2e5c6?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Salmon & Brown Rice Bowl",
    restaurant: "Wok This Way",
    platform: "ZOMATO",
    cuisine: "Japanese",
    mealType: "DINNER",
    calories: 520, proteinG: 42, carbsG: 48, fatG: 16, price: 400,
    isVegetarian: false, isVegan: false, allergens: ["fish", "soy"],
    imageUrl: "https://images.unsplash.com/photo-1562802378-063ec186a863?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Chana Masala with Jeera Rice",
    restaurant: "Punjabi Dhaba",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "DINNER",
    calories: 470, proteinG: 20, carbsG: 68, fatG: 10, price: 160,
    isVegetarian: true, isVegan: true, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Greek Lemon Chicken Souvlaki",
    restaurant: "The Salad Bar",
    platform: "ZOMATO",
    cuisine: "Mediterranean",
    mealType: "DINNER",
    calories: 460, proteinG: 38, carbsG: 28, fatG: 18, price: 350,
    isVegetarian: false, isVegan: false, allergens: ["gluten"],
    imageUrl: "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Baingan Bharta with Multigrain Roti",
    restaurant: "Green Bowl Co",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "DINNER",
    calories: 350, proteinG: 10, carbsG: 48, fatG: 12, price: 160,
    isVegetarian: true, isVegan: true, allergens: ["gluten"],
    imageUrl: "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Egg Curry with Brown Rice",
    restaurant: "The Protein Kitchen",
    platform: "ZOMATO",
    cuisine: "South Indian",
    mealType: "DINNER",
    calories: 470, proteinG: 28, carbsG: 50, fatG: 16, price: 180,
    isVegetarian: false, isVegan: false, allergens: ["egg"],
    imageUrl: "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Stir-fried Broccoli Tofu",
    restaurant: "Wok This Way",
    platform: "SWIGGY",
    cuisine: "Chinese",
    mealType: "DINNER",
    calories: 350, proteinG: 24, carbsG: 28, fatG: 14, price: 230,
    isVegetarian: true, isVegan: true, allergens: ["soy"],
    imageUrl: "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Miso Soup with Edamame & Rice",
    restaurant: "Wok This Way",
    platform: "ZOMATO",
    cuisine: "Japanese",
    mealType: "DINNER",
    calories: 340, proteinG: 16, carbsG: 52, fatG: 6, price: 250,
    isVegetarian: true, isVegan: true, allergens: ["soy"],
    imageUrl: "https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Grilled Chicken with Sweet Potato",
    restaurant: "FreshFit Kitchen",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "DINNER",
    calories: 490, proteinG: 40, carbsG: 42, fatG: 16, price: 330,
    isVegetarian: false, isVegan: false, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=600&q=80",
  },

  // ─── SNACK ──────────────────────────────────────────────────────────────────

  {
    name: "Roasted Chana Chaat",
    restaurant: "Snack Shack",
    platform: "ZOMATO",
    cuisine: "North Indian",
    mealType: "SNACK",
    calories: 180, proteinG: 9, carbsG: 28, fatG: 4, price: 90,
    isVegetarian: true, isVegan: true, allergens: [],
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
    imageUrl: "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Mixed Nuts & Dried Fruit",
    restaurant: "Snack Shack",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "SNACK",
    calories: 200, proteinG: 6, carbsG: 20, fatG: 12, price: 110,
    isVegetarian: true, isVegan: true, allergens: ["nuts"],
    imageUrl: "https://images.unsplash.com/photo-1548017787-e5a3d536a38f?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Boiled Egg & Whole Grain Crackers",
    restaurant: "Morning Fuel Cafe",
    platform: "ZOMATO",
    cuisine: "Continental",
    mealType: "SNACK",
    calories: 190, proteinG: 14, carbsG: 18, fatG: 8, price: 100,
    isVegetarian: false, isVegan: false, allergens: ["egg", "gluten"],
    imageUrl: "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Peanut Butter Banana Smoothie",
    restaurant: "Blend Bar",
    platform: "ZOMATO",
    cuisine: "Healthy Bowls",
    mealType: "SNACK",
    calories: 310, proteinG: 14, carbsG: 38, fatG: 11, price: 160,
    isVegetarian: true, isVegan: true, allergens: ["peanuts"],
    imageUrl: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Edamame with Sea Salt",
    restaurant: "Wok This Way",
    platform: "SWIGGY",
    cuisine: "Japanese",
    mealType: "SNACK",
    calories: 150, proteinG: 12, carbsG: 14, fatG: 5, price: 140,
    isVegetarian: true, isVegan: true, allergens: ["soy"],
    imageUrl: "https://images.unsplash.com/photo-1590080876306-3c4b38d31ec5?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Hummus with Carrot Sticks",
    restaurant: "The Salad Bar",
    platform: "ZOMATO",
    cuisine: "Mediterranean",
    mealType: "SNACK",
    calories: 160, proteinG: 7, carbsG: 20, fatG: 6, price: 120,
    isVegetarian: true, isVegan: true, allergens: ["sesame"],
    imageUrl: "https://images.unsplash.com/photo-1542014740373-51ad6425a7e6?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Cottage Cheese (Paneer) Cubes",
    restaurant: "The Protein Kitchen",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "SNACK",
    calories: 170, proteinG: 16, carbsG: 4, fatG: 10, price: 130,
    isVegetarian: true, isVegan: false, allergens: ["dairy"],
    imageUrl: "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Apple Slices with Almond Butter",
    restaurant: "Cafe Green",
    platform: "ZOMATO",
    cuisine: "Healthy Bowls",
    mealType: "SNACK",
    calories: 210, proteinG: 5, carbsG: 28, fatG: 10, price: 130,
    isVegetarian: true, isVegan: true, allergens: ["nuts"],
    imageUrl: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Roasted Makhana (Fox Nuts)",
    restaurant: "Snack Shack",
    platform: "SWIGGY",
    cuisine: "North Indian",
    mealType: "SNACK",
    calories: 140, proteinG: 5, carbsG: 28, fatG: 2, price: 80,
    isVegetarian: true, isVegan: true, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Whey Protein Shake",
    restaurant: "Blend Bar",
    platform: "SWIGGY",
    cuisine: "Healthy Bowls",
    mealType: "SNACK",
    calories: 160, proteinG: 24, carbsG: 8, fatG: 3, price: 150,
    isVegetarian: true, isVegan: false, allergens: ["dairy"],
    imageUrl: "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Green Moong Sprouts Bowl",
    restaurant: "FreshFit Kitchen",
    platform: "ZOMATO",
    cuisine: "Healthy Bowls",
    mealType: "SNACK",
    calories: 145, proteinG: 10, carbsG: 22, fatG: 2, price: 100,
    isVegetarian: true, isVegan: true, allergens: [],
    imageUrl: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80",
  },
  {
    name: "Greek Yogurt with Honey & Walnuts",
    restaurant: "Cafe Green",
    platform: "SWIGGY",
    cuisine: "Mediterranean",
    mealType: "SNACK",
    calories: 230, proteinG: 12, carbsG: 22, fatG: 10, price: 160,
    isVegetarian: true, isVegan: false, allergens: ["dairy", "nuts"],
    imageUrl: "https://images.unsplash.com/photo-1571748982800-fa51082c2224?auto=format&fit=crop&w=600&q=80",
  },
];

function healthScoreFor(m: (typeof sampleMeals)[number]): number {
  // Reward high protein-to-calorie ratio, penalize high fat share
  const proteinRatio = (m.proteinG * 4) / m.calories;
  const fatRatio = (m.fatG * 9) / m.calories;
  const score = 100 * proteinRatio - 40 * fatRatio + 40;
  return Math.max(0, Math.min(100, Math.round(score)));
}

/**
 * Guard: fail loudly if any meal is missing imageUrl.
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
  validateImageUrls(sampleMeals);

  console.log(`Seeding ${sampleMeals.length} meals...`);
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
  const byType = sampleMeals.reduce<Record<string, number>>((acc, m) => {
    acc[m.mealType] = (acc[m.mealType] || 0) + 1;
    return acc;
  }, {});

  console.log(`\n✓ Seeded ${sampleMeals.length} meals across ${uniqueCuisines.size} cuisines`);
  console.log(`  Breakdown by meal type:`);
  Object.entries(byType).forEach(([type, count]) => {
    console.log(`    ${type.padEnd(10)}: ${count} meals`);
  });
  console.log(`  All meals have imageUrl ✓`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
