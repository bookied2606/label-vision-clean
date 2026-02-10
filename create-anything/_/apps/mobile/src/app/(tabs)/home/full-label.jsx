import { View, Text, useColorScheme, ScrollView } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { useRouter } from "expo-router";
import { ArrowLeft, Volume2 } from "lucide-react-native";
import HapticButton from "@/components/HapticButton";
import { speak } from "@/utils/tts";
import { useScanStore } from "@/utils/scanStore";
import {
  useFonts,
  Inter_600SemiBold,
  Inter_500Medium,
  Inter_400Regular,
} from "@expo-google-fonts/inter";

export default function FullLabelScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const { currentScan } = useScanStore();

  const [fontsLoaded] = useFonts({
    Inter_600SemiBold,
    Inter_500Medium,
    Inter_400Regular,
  });

  if (!fontsLoaded || !currentScan) {
    return null;
  }

  const playFullLabel = () => {
    const productName = currentScan.product_name || currentScan.product || "Unknown";
    const brand = currentScan.brand || currentScan.manufacturer || "";
    const expiry = currentScan.expiry_date || currentScan.expiry || "Not found";
    const mfg = currentScan.mfg_date || currentScan.mfgDate || "";
    const ingredients = currentScan.ingredients?.length > 0 ? currentScan.ingredients.join(", ") : "Not listed";
    const warnings = currentScan.warnings?.length > 0 ? currentScan.warnings.join(". ") : "None";
    
    const fullText = `Product: ${productName}. ${brand ? `Brand: ${brand}. ` : ""}${mfg ? `Manufactured: ${mfg}. ` : ""}Expires: ${expiry}. Ingredients: ${ingredients}. Warnings: ${warnings}.`;
    speak(fullText);
  };

  return (
    <View style={{ flex: 1, backgroundColor: isDark ? "#121212" : "#FFFFFF" }}>
      <StatusBar style={isDark ? "light" : "dark"} />

      {/* Header */}
      <View
        style={{
          paddingTop: insets.top + 16,
          paddingHorizontal: 20,
          paddingBottom: 16,
          backgroundColor: isDark ? "#121212" : "#FFFFFF",
          borderBottomWidth: 1,
          borderBottomColor: isDark ? "#333333" : "#F0F0F0",
          flexDirection: "row",
          alignItems: "center",
        }}
      >
        <HapticButton onPress={() => router.back()} style={{ marginRight: 12 }}>
          <ArrowLeft size={28} color={isDark ? "#FFFFFF" : "#000000"} />
        </HapticButton>
        <Text
          style={{
            fontSize: 24,
            fontFamily: "Inter_600SemiBold",
            color: isDark ? "#FFFFFF" : "#000000",
            flex: 1,
          }}
        >
          Full Label
        </Text>
        <HapticButton onPress={playFullLabel}>
          <Volume2 size={28} color="#3B82F6" />
        </HapticButton>
      </View>

      {/* Content */}
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{
          paddingHorizontal: 20,
          paddingTop: 20,
          paddingBottom: insets.bottom + 20,
        }}
        showsVerticalScrollIndicator={false}
      >
        {/* Product Name */}
        <View style={{ marginBottom: 24 }}>
          <Text
            style={{
              fontSize: 16,
              fontFamily: "Inter_500Medium",
              color: isDark ? "#9CA3AF" : "#6B7280",
              marginBottom: 8,
            }}
          >
            Product Name
          </Text>
          <Text
            style={{
              fontSize: 20,
              fontFamily: "Inter_600SemiBold",
              color: isDark ? "#FFFFFF" : "#000000",
              lineHeight: 28,
            }}
          >
            {currentScan.product_name || currentScan.product || "Unknown"}
          </Text>
        </View>

        {/* Brand */}
        {(currentScan.brand || currentScan.manufacturer) && (
          <View style={{ marginBottom: 24 }}>
            <Text
              style={{
                fontSize: 16,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#9CA3AF" : "#6B7280",
                marginBottom: 6,
              }}
            >
              Brand
            </Text>
            <Text
              style={{
                fontSize: 18,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#D1D5DB" : "#374151",
              }}
            >
              {currentScan.brand || currentScan.manufacturer}
            </Text>
          </View>
        )}

        {/* Expiry Date */}
        {(currentScan.expiry_date || currentScan.expiry) && (
          <View style={{ marginBottom: 24 }}>
            <Text
              style={{
                fontSize: 16,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#9CA3AF" : "#6B7280",
                marginBottom: 6,
              }}
            >
              Expiry Date
            </Text>
            <Text
              style={{
                fontSize: 18,
                fontFamily: "Inter_600SemiBold",
                color: "#EF4444",
              }}
            >
              {currentScan.expiry_date || currentScan.expiry}
            </Text>
          </View>
        )}

        {/* Manufacturing Date */}
        {(currentScan.mfg_date || currentScan.mfgDate) && (
          <View style={{ marginBottom: 24 }}>
            <Text
              style={{
                fontSize: 16,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#9CA3AF" : "#6B7280",
                marginBottom: 6,
              }}
            >
              Manufacturing Date
            </Text>
            <Text
              style={{
                fontSize: 18,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#D1D5DB" : "#374151",
              }}
            >
              {currentScan.mfg_date || currentScan.mfgDate}
            </Text>
          </View>
        )}

        {/* Ingredients */}
        {currentScan.ingredients && currentScan.ingredients.length > 0 && (
          <View style={{ marginBottom: 24 }}>
            <Text
              style={{
                fontSize: 16,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#9CA3AF" : "#6B7280",
                marginBottom: 8,
              }}
            >
              Ingredients
            </Text>
            <Text
              style={{
                fontSize: 14,
                fontFamily: "Inter_400Regular",
                color: isDark ? "#D1D5DB" : "#374151",
                lineHeight: 22,
              }}
            >
              {currentScan.ingredients.join(", ")}
            </Text>
          </View>
        )}

        {/* Warnings */}
        {currentScan.warnings && currentScan.warnings.length > 0 && (
          <View style={{ marginBottom: 24 }}>
            <Text
              style={{
                fontSize: 16,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#9CA3AF" : "#6B7280",
                marginBottom: 8,
              }}
            >
              ⚠️ Warnings
            </Text>
            {currentScan.warnings.map((warning, idx) => (
              <Text
                key={idx}
                style={{
                  fontSize: 14,
                  fontFamily: "Inter_400Regular",
                  color: "#F59E0B",
                  marginBottom: 6,
                  paddingLeft: 8,
                }}
              >
                • {warning}
              </Text>
            ))}
          </View>
        )}

        {/* Confidence */}
        {currentScan.confidence !== undefined && (
          <View style={{ marginBottom: 24 }}>
            <Text
              style={{
                fontSize: 16,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#9CA3AF" : "#6B7280",
                marginBottom: 6,
              }}
            >
              Scan Confidence
            </Text>
            <View
              style={{
                backgroundColor: isDark ? "#333333" : "#F6F6F6",
                borderRadius: 8,
                padding: 12,
                flexDirection: "row",
                alignItems: "center",
              }}
            >
              <Text
                style={{
                  fontSize: 24,
                  fontFamily: "Inter_600SemiBold",
                  color:
                    currentScan.confidence > 0.7
                      ? "#10B981"
                      : currentScan.confidence > 0.4
                      ? "#F59E0B"
                      : "#EF4444",
                  marginRight: 12,
                }}
              >
                {(currentScan.confidence * 100).toFixed(0)}%
              </Text>
              <View
                style={{
                  flex: 1,
                  height: 8,
                  backgroundColor: isDark ? "#555555" : "#E5E7EB",
                  borderRadius: 4,
                  overflow: "hidden",
                }}
              >
                <View
                  style={{
                    height: "100%",
                    width: `${currentScan.confidence * 100}%`,
                    backgroundColor:
                      currentScan.confidence > 0.7
                        ? "#10B981"
                        : currentScan.confidence > 0.4
                        ? "#F59E0B"
                        : "#EF4444",
                  }}
                />
              </View>
            </View>
          </View>
        )}

        {/* Raw OCR Text (for debugging) */}
        {(currentScan.raw_ocr_front || currentScan.raw_ocr_back) && (
          <View style={{ marginBottom: 24, borderTopWidth: 1, borderTopColor: isDark ? "#333333" : "#E5E7EB", paddingTop: 16 }}>
            <Text
              style={{
                fontSize: 16,
                fontFamily: "Inter_500Medium",
                color: isDark ? "#9CA3AF" : "#6B7280",
                marginBottom: 8,
              }}
            >
              🔍 Raw OCR Data
            </Text>
            {currentScan.raw_ocr_front && (
              <View style={{ marginBottom: 12 }}>
                <Text
                  style={{
                    fontSize: 12,
                    fontFamily: "Inter_500Medium",
                    color: "#3B82F6",
                    marginBottom: 4,
                  }}
                >
                  Front Side:
                </Text>
                <Text
                  style={{
                    fontSize: 12,
                    fontFamily: "Inter_400Regular",
                    color: isDark ? "#999999" : "#999999",
                    lineHeight: 16,
                    backgroundColor: isDark ? "#0F0F0F" : "#F9F9F9",
                    padding: 8,
                    borderRadius: 6,
                  }}
                >
                  {currentScan.raw_ocr_front.substring(0, 200)}
                  {currentScan.raw_ocr_front.length > 200 ? "..." : ""}
                </Text>
              </View>
            )}
            {currentScan.raw_ocr_back && (
              <View>
                <Text
                  style={{
                    fontSize: 12,
                    fontFamily: "Inter_500Medium",
                    color: "#3B82F6",
                    marginBottom: 4,
                  }}
                >
                  Back Side:
                </Text>
                <Text
                  style={{
                    fontSize: 12,
                    fontFamily: "Inter_400Regular",
                    color: isDark ? "#999999" : "#999999",
                    lineHeight: 16,
                    backgroundColor: isDark ? "#0F0F0F" : "#F9F9F9",
                    padding: 8,
                    borderRadius: 6,
                  }}
                >
                  {currentScan.raw_ocr_back.substring(0, 200)}
                  {currentScan.raw_ocr_back.length > 200 ? "..." : ""}
                </Text>
              </View>
            )}
          </View>
        )}
      </ScrollView>
    </View>
  );
}
