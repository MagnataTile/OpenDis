// ui/theme/Theme.kt
package com.magnatatitle.opendis.ui.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColors = darkColorScheme(
    primary = Color(0xFF5865F2),
    secondary = Color(0xFF3ba55d),
    background = Color(0xFF1e1e2e),
    surface = Color(0xFF2f3136),
    onPrimary = Color.White,
    onSecondary = Color.White,
    onBackground = Color(0xFFcccccc),
    onSurface = Color(0xFFcccccc),
    error = Color(0xFFed4245),
    onError = Color.White
)

@Composable
fun OpenDisTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColors,
        content = content
    )
}
