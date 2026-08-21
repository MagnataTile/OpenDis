// ui/screens/ProfileSelectionScreen.kt
package com.magnatatitle.opendis.ui.screens

import android.app.Activity
import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.magnatatitle.opendis.viewmodel.OpenDisViewModel
import java.io.File

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileSelectionScreen(
    viewModel: OpenDisViewModel,
    onProfileSelected: () -> Unit,
    onRandomVpn: () -> Unit
) {
    val profiles by viewModel.profiles.collectAsState()
    val selectedProfile by viewModel.selectedProfile.collectAsState()
    val context = LocalContext.current

    var expanded by remember { mutableStateOf(false) }

    // Launcher para importar .ovpn
    val importLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val uri = result.data?.data
            if (uri != null) {
                try {
                    val inputStream = context.contentResolver.openInputStream(uri)
                    val fileName = "imported_${System.currentTimeMillis()}.ovpn"
                    val tempFile = File(context.cacheDir, fileName)
                    
                    inputStream?.use { input ->
                        tempFile.outputStream().use { output ->
                            input.copyTo(output)
                        }
                    }
                    
                    // Usa o ViewModel para importar e selecionar
                    viewModel.importAndSelectProfile(tempFile)
                } catch (e: Exception) {
                    // Log error if needed
                }
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        "🔐 Configuração VPN",
                        fontWeight = FontWeight.Bold
                    )
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF1e1e2e),
                    titleContentColor = Color.White
                )
            )
        },
        containerColor = Color(0xFF1e1e2e)
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(Modifier.height(12.dp))

            // ─── Botão VPN Aleatória ───
            Button(
                onClick = onRandomVpn,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF3ba55d)
                ),
                shape = RoundedCornerShape(28.dp)
            ) {
                Icon(Icons.Default.Shuffle, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("VPN ALEATÓRIA VPNBook", fontWeight = FontWeight.Bold, fontSize = 15.sp)
            }

            Spacer(Modifier.height(16.dp))

            // ─── Separador ───
            Text(
                "— ou selecione manualmente —",
                color = Color(0xFF666675),
                fontSize = 13.sp
            )

            Spacer(Modifier.height(12.dp))

            // ─── Dropdown de perfis ───
            if (profiles.isNotEmpty()) {
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = it }
                ) {
                    OutlinedTextField(
                        value = selectedProfile?.name ?: "Selecione um perfil",
                        onValueChange = {},
                        readOnly = true,
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFF5865F2),
                            unfocusedBorderColor = Color(0xFF404040),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        ),
                        shape = RoundedCornerShape(8.dp)
                    )

                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        profiles.forEach { profile ->
                            DropdownMenuItem(
                                text = { Text(profile.name) },
                                onClick = {
                                    viewModel.selectProfile(profile)
                                    expanded = false
                                }
                            )
                        }
                    }
                }
            } else {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF2f3136)
                    )
                ) {
                    Text(
                        "Nenhum .ovpn manual encontrado.\nAdicione um perfil para começar.",
                        modifier = Modifier.padding(16.dp),
                        color = Color(0xFF666675),
                        fontSize = 12.sp
                    )
                }
            }

            Spacer(Modifier.height(12.dp))

            // ─── Botão Importar ───
            OutlinedButton(
                onClick = {
                    val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = "*/*"
                    }
                    importLauncher.launch(intent)
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = Color.White
                ),
                border = ButtonDefaults.outlinedButtonBorder.copy(
                    brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF404040))
                )
            ) {
                Icon(Icons.Default.FileOpen, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Adicionar / importar .ovpn")
            }

            Spacer(Modifier.height(8.dp))

            // ─── Info do perfil ───
            if (selectedProfile != null) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF2f3136)
                    )
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        val info = if (selectedProfile!!.requiresAuth)
                            "🔐 Este perfil solicita usuário e senha."
                        else
                            "✅ Este perfil não solicita credenciais."

                        Text(
                            info,
                            color = if (selectedProfile!!.requiresAuth)
                                Color(0xFFf0a030)
                            else
                                Color(0xFF57F287),
                            fontSize = 12.sp
                        )
                    }
                }
            }

            Spacer(Modifier.weight(1f))

            // ─── Botão Continuar ───
            Button(
                onClick = {
                    onProfileSelected()
                },
                enabled = selectedProfile != null,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF5865F2),
                    disabledContainerColor = Color(0xFF404040)
                ),
                shape = RoundedCornerShape(26.dp)
            ) {
                Text(
                    "➡️ CONTINUAR",
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp
                )
            }

            Spacer(Modifier.height(12.dp))
        }
    }
}
