// ui/screens/CredentialsScreen.kt
package com.magnatatitle.opendis.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.magnatatitle.opendis.viewmodel.OpenDisViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CredentialsScreen(
    viewModel: OpenDisViewModel,
    onContinue: () -> Unit,
    onBack: () -> Unit
) {
    // Observa as credenciais salvas para preenchimento automático
    val savedCreds by viewModel.savedCredentials.collectAsState()
    
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var rememberCreds by remember { mutableStateOf(true) }
    var showPassword by remember { mutableStateOf(false) }

    // Efeito para preencher quando as credenciais forem carregadas
    LaunchedEffect(savedCreds) {
        savedCreds?.let {
            username = it.username
            password = it.password
            rememberCreds = true
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text("🔐 Credenciais OpenVPN", fontWeight = FontWeight.Bold)
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Voltar")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF1e1e2e),
                    titleContentColor = Color.White,
                    navigationIconContentColor = Color.White
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
            Spacer(Modifier.height(24.dp))

            Text(
                "Este perfil exige autenticação.\nInforme as credenciais do OpenVPN.",
                color = Color(0xFFa0a0b0),
                fontSize = 14.sp,
                lineHeight = 20.sp
            )

            Spacer(Modifier.height(24.dp))

            // ─── Usuário ───
            OutlinedTextField(
                value = username,
                onValueChange = { username = it },
                label = { Text("Usuário") },
                leadingIcon = { Icon(Icons.Default.Person, contentDescription = null) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Color(0xFF5865F2),
                    unfocusedBorderColor = Color(0xFF404040),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedLabelColor = Color(0xFF5865F2),
                    unfocusedLabelColor = Color(0xFF888888)
                ),
                shape = RoundedCornerShape(8.dp)
            )

            Spacer(Modifier.height(12.dp))

            // ─── Senha ───
            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text("Senha") },
                leadingIcon = { Icon(Icons.Default.Lock, contentDescription = null) },
                trailingIcon = {
                    IconButton(onClick = { showPassword = !showPassword }) {
                        Icon(
                            if (showPassword) Icons.Default.VisibilityOff
                            else Icons.Default.Visibility,
                            contentDescription = "Mostrar senha"
                        )
                    }
                },
                visualTransformation = if (showPassword)
                    VisualTransformation.None
                else
                    PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Color(0xFF5865F2),
                    unfocusedBorderColor = Color(0xFF404040),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedLabelColor = Color(0xFF5865F2),
                    unfocusedLabelColor = Color(0xFF888888)
                ),
                shape = RoundedCornerShape(8.dp)
            )

            Spacer(Modifier.height(16.dp))

            // ─── Lembrar credenciais ───
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(
                    checked = rememberCreds,
                    onCheckedChange = { rememberCreds = it },
                    colors = CheckboxDefaults.colors(
                        checkedColor = Color(0xFF5865F2)
                    )
                )
                Text("Lembrar credenciais", color = Color(0xFFcccccc), fontSize = 14.sp)
            }

            Text(
                "🔒 As credenciais são armazenadas de forma criptografada.",
                color = Color(0xFF666675),
                fontSize = 10.sp
            )

            Spacer(Modifier.weight(1f))

            // ─── Continuar ───
            Button(
                onClick = {
                    viewModel.submitCredentials(username, password, rememberCreds)
                    onContinue()
                },
                enabled = username.isNotBlank() && password.isNotBlank(),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF5865F2),
                    disabledContainerColor = Color(0xFF404040)
                ),
                shape = RoundedCornerShape(26.dp)
            ) {
                Text("➡️ CONTINUAR", fontWeight = FontWeight.Bold, fontSize = 16.sp)
            }

            Spacer(Modifier.height(12.dp))

            // ─── Voltar ───
            TextButton(
                onClick = onBack,
                modifier = Modifier.height(40.dp)
            ) {
                Text("← VOLTAR", color = Color(0xFF888888), fontWeight = FontWeight.Bold)
            }

            Spacer(Modifier.height(16.dp))
        }
    }
}
