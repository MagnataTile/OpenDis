// ui/screens/CompletedScreen.kt
package com.magnatatitle.opendis.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.magnatatitle.opendis.viewmodel.OpenDisViewModel

@Composable
fun CompletedScreen(
    viewModel: OpenDisViewModel,
    onFinish: () -> Unit
) {
    val logs by viewModel.logs.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(
                Icons.Default.CheckCircle,
                contentDescription = null,
                tint = Color(0xFF57F287),
                modifier = Modifier.size(80.dp)
            )

            Spacer(Modifier.height(16.dp))

            Text(
                "✅ CONCLUÍDO",
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF57F287)
            )

            Spacer(Modifier.height(8.dp))

            Text(
                "Operação finalizada com sucesso!",
                color = Color(0xFFa0a0b0),
                fontSize = 14.sp
            )

            Spacer(Modifier.height(24.dp))

            // Últimos logs
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 200.dp),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF12121a)
                ),
                shape = RoundedCornerShape(8.dp)
            ) {
                LazyColumn(
                    modifier = Modifier.padding(8.dp)
                ) {
                    items(logs.takeLast(10)) { log ->
                        Text(
                            text = log,
                            color = Color(0xFF8e9297),
                            fontSize = 11.sp,
                            fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace,
                            modifier = Modifier.padding(vertical = 1.dp)
                        )
                    }
                }
            }

            Spacer(Modifier.height(24.dp))

            Button(
                onClick = onFinish,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF3ba55d)
                ),
                shape = RoundedCornerShape(26.dp)
            ) {
                Text("🔄 Novo ciclo", fontWeight = FontWeight.Bold, fontSize = 16.sp)
            }
        }
    }
}
