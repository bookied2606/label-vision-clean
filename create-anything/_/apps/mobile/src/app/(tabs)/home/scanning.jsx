import { View, Text, StatusBar, Pressable, Image as RNImage } from "react-native";
import { useRouter } from "expo-router";
import { useColorScheme } from "react-native";
import { useEffect, useRef, useState } from "react";
import { CheckCircle, AlertCircle, RotateCcw } from "lucide-react-native";
import { useFonts } from "expo-font";
import { CameraView, useCameraPermissions } from "expo-camera";
import { speak } from "@/utils/tts";
import { scanImages, testConnection } from "@/utils/api";
import { useScanStore } from "@/utils/scanStore";
import {
  Inter_600SemiBold,
  Inter_500Medium,
} from "@expo-google-fonts/inter";

export default function ScanningScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const { settings, setCurrentScan } = useScanStore();

  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef(null);
  const captureTimeoutRef = useRef(null);
  const [capturing, setCapturing] = useState(false);
  const [connected, setConnected] = useState(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [debugMsg, setDebugMsg] = useState("Camera loading...");

  // Multi-side capture state
  const [frontImageUri, setFrontImageUri] = useState(null);
  const [backImageUri, setBackImageUri] = useState(null);
  const [currentSide, setCurrentSide] = useState("front"); // "front" or "back"

  const [fontsLoaded] = useFonts({
    Inter_600SemiBold,
    Inter_500Medium,
  });

  const autoCapturePhoto = async () => {
    if (capturing || !cameraReady || !cameraRef.current) {
      console.log("⚠️ Cannot capture:", { capturing, cameraReady, hasRef: !!cameraRef.current });
      return;
    }

    try {
      setCapturing(true);
      setDebugMsg("📸 Capturing...");
      console.log(`📸 Capturing ${currentSide} side...`);

      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: false,
      });

      console.log(`✅ ${currentSide.toUpperCase()} photo captured:`, photo.uri);
      setDebugMsg("Processing...");
      await processImage(photo.uri);
    } catch (error) {
      console.error("❌ Capture error:", error);
      setDebugMsg("❌ Capture error");
      alert("Camera error: " + error.message);
      setCapturing(false);
    }
  };

  const manualCapture = async () => {
    console.log(`📸 Manual capture triggered for ${currentSide}`);
    // Clear any auto-capture timeout
    if (captureTimeoutRef.current) {
      clearTimeout(captureTimeoutRef.current);
      captureTimeoutRef.current = null;
    }
    autoCapturePhoto();
  };

  const processImage = async (imageUri) => {
    try {
      if (currentSide === "front") {
        // First side (front) captured - move to back
        console.log("✅ Front side captured, waiting for back side");
        setFrontImageUri(imageUri);
        setCurrentSide("back");
        setDebugMsg("✅ Front captured! Now FLIP and point at BACK side\n(This is where expiry date usually is)");
        setCapturing(false);
        
        if (settings.voiceEnabled) {
          speak("Front side captured, now flip the label and scan the back side");
        }
        
        // DO NOT auto-capture back - wait for user to tap
        
      } else if (currentSide === "back") {
        // Both sides captured - send to backend
        console.log("✅ Back side captured, sending both to backend");
        setBackImageUri(imageUri);
        setDebugMsg("Uploading both sides to backend...");
        
        try {
          console.log("📤 Sending front + back to backend...");
          const scanResult = await scanImages(frontImageUri, imageUri);
          console.log("✅ Backend response:", scanResult);
          setCurrentScan(scanResult);
          setCapturing(false);
          router.replace("/(tabs)/home/result");
        } catch (apiError) {
          console.error("❌ Backend failed:", apiError);
          alert("Backend error: " + apiError.message);
          setCapturing(false);
        }
      }
    } catch (e) {
      console.error("❌ Process error:", e);
      alert("Error: " + e.message);
      setCapturing(false);
    }
  };

  const resetCapture = () => {
    console.log("🔄 Resetting capture");
    setFrontImageUri(null);
    setBackImageUri(null);
    setCurrentSide("front");
    setCameraReady(false);
    setDebugMsg("Camera loading...");
    setCapturing(false);
  };

  useEffect(() => {
    console.log("🎬 ScanningScreen mounted");
    
    if (settings.voiceEnabled) {
      speak("Point camera at front side of label to auto-scan");
    }

    if (permission?.status !== "granted") {
      console.log("📹 Requesting camera permission...");
      requestPermission();
    } else {
      console.log("✅ Camera permission already granted");
    }

    testConnection()
      .then(() => {
        console.log("✅ Backend connected");
        setConnected(true);
      })
      .catch((err) => {
        console.error("❌ Backend unreachable:", err);
        setConnected(false);
      });

    return () => {
      if (captureTimeoutRef.current) {
        clearTimeout(captureTimeoutRef.current);
      }
    };
  }, [settings.voiceEnabled, permission?.status, requestPermission]);

  if (!fontsLoaded) {
    return null;
  }

  if (!permission?.granted) {
    return (
      <View
        style={{
          flex: 1,
          justifyContent: "center",
          alignItems: "center",
          backgroundColor: isDark ? "#111827" : "#F9FAFB",
        }}
      >
        <Text style={{ fontSize: 16, marginBottom: 16, color: isDark ? "#FFF" : "#000" }}>
          Camera access required
        </Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: isDark ? "#111827" : "#F9FAFB" }}>
      <StatusBar barStyle={isDark ? "light-content" : "dark-content"} />

      <CameraView
        ref={cameraRef}
        style={{ flex: 1 }}
        facing="back"
        onCameraReady={() => {
          console.log("📷 Camera onCameraReady fired!");
          setCameraReady(true);
          
          // Only auto-capture for FRONT side on first load
          if (currentSide === "front" && !frontImageUri) {
            setDebugMsg("Camera ready - tap to capture FRONT side");
            console.log("📷 Camera ready - waiting for manual front capture");
          } else {
            setDebugMsg(`Camera ready - tap to capture ${currentSide.toUpperCase()} side`);
          }
        }}
      >
        <View
          style={{
            flex: 1,
            justifyContent: "center",
            alignItems: "center",
            backgroundColor: "rgba(0, 0, 0, 0.3)",
          }}
        >
          {/* Show captured images as thumbnails */}
          <View
            style={{
              flexDirection: "row",
              gap: 12,
              marginBottom: 30,
              paddingHorizontal: 20,
            }}
          >
            {frontImageUri && (
              <View
                style={{
                  width: 60,
                  height: 60,
                  borderRadius: 8,
                  borderWidth: 2,
                  borderColor: "#10B981",
                  overflow: "hidden",
                }}
              >
                <RNImage
                  source={{ uri: frontImageUri }}
                  style={{ width: "100%", height: "100%" }}
                />
              </View>
            )}
            {backImageUri && (
              <View
                style={{
                  width: 60,
                  height: 60,
                  borderRadius: 8,
                  borderWidth: 2,
                  borderColor: "#10B981",
                  overflow: "hidden",
                }}
              >
                <RNImage
                  source={{ uri: backImageUri }}
                  style={{ width: "100%", height: "100%" }}
                />
              </View>
            )}
          </View>

          <View
            style={{
              width: "80%",
              aspectRatio: 1,
              borderWidth: 3,
              borderColor: "#3B82F6",
              borderRadius: 20,
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Text
              style={{
                color: "#3B82F6",
                fontSize: 18,
                fontFamily: "Inter_500Medium",
              }}
            >
              Point at {currentSide.toUpperCase()}
            </Text>
            {!capturing && (
              <>
                <Text
                  style={{
                    color: "#9CA3AF",
                    fontSize: 12,
                    marginTop: 12,
                    textAlign: "center",
                  }}
                >
                  Position label to fill this frame
                </Text>
                <Text
                  style={{
                    color: "#9CA3AF",
                    fontSize: 11,
                    marginTop: 8,
                    textAlign: "center",
                    maxWidth: "90%",
                  }}
                >
                  • Keep straight and centered{"\n"}• Good lighting required{"\n"}• Focus on text clarity
                </Text>
              </>
            )}
          </View>

          {/* Manual capture button as backup */}
          <Pressable
            onPress={manualCapture}
            disabled={capturing}
            style={{
              marginTop: 40,
              backgroundColor: "#EF4444",
              paddingHorizontal: 30,
              paddingVertical: 12,
              borderRadius: 8,
            }}
          >
            <Text style={{ color: "#FFF", fontWeight: "bold", fontSize: 16 }}>
              {capturing ? "Processing..." : "Tap to Capture"}
            </Text>
          </Pressable>

          {/* Reset button if front is captured */}
          {frontImageUri && (
            <Pressable
              onPress={resetCapture}
              disabled={capturing}
              style={{
                marginTop: 12,
                backgroundColor: "#6B7280",
                paddingHorizontal: 20,
                paddingVertical: 8,
                borderRadius: 8,
                flexDirection: "row",
                alignItems: "center",
                gap: 6,
              }}
            >
              <RotateCcw size={16} color="#FFF" />
              <Text style={{ color: "#FFF", fontWeight: "bold", fontSize: 14 }}>
                Reset
              </Text>
            </Pressable>
          )}
        </View>
      </CameraView>

      <View
        style={{
          position: "absolute",
          bottom: 40,
          left: 0,
          right: 0,
          alignItems: "center",
        }}
      >
        {/* Debug message */}
        <View style={{ marginBottom: 16, paddingHorizontal: 20 }}>
          <Text style={{ color: "#FFF", fontSize: 12, textAlign: "center" }}>
            {debugMsg}
          </Text>
        </View>

        {connected === false && (
          <View style={{ marginBottom: 12, paddingHorizontal: 20 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <AlertCircle size={20} color="#EF4444" />
              <Text style={{ color: "#EF4444", fontSize: 14, flex: 1 }}>
                Backend unreachable
              </Text>
            </View>
          </View>
        )}
        {connected === true && (
          <View style={{ marginBottom: 12 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
              <CheckCircle size={16} color="#10B981" />
              <Text style={{ color: "#10B981", fontSize: 12 }}>
                Connected
              </Text>
            </View>
          </View>
        )}
      </View>
    </View>
  );
}
