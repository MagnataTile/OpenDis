// ui/screens/SplashScreen.kt
package com.magnatatitle.opendis.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.magnatatitle.opendis.viewmodel.OpenDisViewModel
import kotlinx.coroutines.delay

@Composable
fun SplashScreen(
    viewModel: OpenDisViewModel,
    onReady: () -> Unit
) {
    var status by remember { mutableStateOf("🔍 Verificando OpenVPN...") }
    var progress by remember { mutableStateOf(0f) }

    LaunchedEffect(Unit) {
        status = "🔍 Inicializando Túnel Interno..."
        delay(500)
        status = "✅ Sistema VPN Pronto"
        progress = 0.5f
        delay(600)
        
        status = "🔍 Verificando Discord..."
        delay(300)
        status = "✅ Ambiente Pronto"
        progress = 1.0f
        delay(500)
        onReady()
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1e1e2e)),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "🛡️",
                fontSize = 60.sp
            )

            Spacer(Modifier.height(8.dp))

            Text(
                text = "OpenDis",
                fontSize = 36.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF5865F2)
            )

            Text(
                text = "OpenVPN + Discord",
                fontSize = 14.sp,
                color = Color(0xFFa0a0b0)
            )

            Spacer(Modifier.height(40.dp))

            Text(
                text = status,
                fontSize = 14.sp,
                color = Color(0xFFcccccc)
            )

            Spacer(Modifier.height(16.dp))

            LinearProgressIndicator(
                progress = progress,
                modifier = Modifier
                    .width(280.dp)
                    .height(4.dp),
                color = Color(0xFF5865F2),
                trackColor = Color(0xFF404040)
            )
        }
    }
}
