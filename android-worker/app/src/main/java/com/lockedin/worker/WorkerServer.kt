package com.lockedin.worker

import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.ServerSocket
import java.net.Socket

class WorkerServer(private val port: Int = 8765) {
    @Volatile
    private var running = false
    private var serverSocket: ServerSocket? = null
    private var serverThread: Thread? = null

    fun start() {
        if (running) return
        running = true

        serverThread = Thread {
            try {
                serverSocket = ServerSocket(port)
                println("LOCKEDIN WORKER listening on 0.0.0.0:$port")

                while (running) {
                    val socket = serverSocket?.accept() ?: break
                    Thread {
                        handleClient(socket)
                    }.start()
                }
            } catch (e: Exception) {
                if (running) {
                    println("Worker server error: ${e.message}")
                }
            }
        }.apply {
            start()
        }
    }

    fun stop() {
        running = false
        try {
            serverSocket?.close()
        } catch (_: Exception) {
        }
        serverSocket = null
        serverThread = null
    }

    private fun handleClient(socket: Socket) {
        socket.use { client ->
            try {
                val reader = BufferedReader(InputStreamReader(client.getInputStream()))
                val requestLine = reader.readLine() ?: return

                val headers = mutableMapOf<String, String>()
                var line: String?

                while (reader.readLine().also { line = it } != null) {
                    if (line!!.isEmpty()) break

                    val separator = line!!.indexOf(':')
                    if (separator > 0) {
                        val key = line!!.substring(0, separator).trim().lowercase()
                        val value = line!!.substring(separator + 1).trim()
                        headers[key] = value
                    }
                }

                val contentLength = headers["content-length"]?.toIntOrNull() ?: 0
                val body = CharArray(contentLength)

                if (contentLength > 0) {
                    var totalRead = 0
                    while (totalRead < contentLength) {
                        val count = reader.read(body, totalRead, contentLength - totalRead)
                        if (count <= 0) break
                        totalRead += count
                    }
                }

                val requestBody = String(body)

                val response = when {
                    requestLine.startsWith("POST /infer") -> handleInference(requestBody)
                    else -> jsonResponse(
                        404,
                        JSONObject().put("error", "Not found")
                    )
                }

                client.getOutputStream().bufferedWriter().use { writer ->
                    writer.write(response)
                    writer.flush()
                }

                println("LOCKEDIN request: $requestLine")
                println("LOCKEDIN body: $requestBody")
            } catch (e: Exception) {
                println("Client error: ${e.message}")
            }
        }
    }

    private fun handleInference(body: String): String {
        return try {
            val request = JSONObject(body)
            val goal = request.optString("goal")
            val activity = request.optString("activity")

            jsonResponse(
                200,
                JSONObject()
                    .put("status", "received")
                    .put("worker", "oneplus-11")
                    .put("goal", goal)
                    .put("activity", activity)
            )
        } catch (e: Exception) {
            jsonResponse(
                400,
                JSONObject().put("error", e.message ?: "Invalid JSON")
            )
        }
    }

    private fun jsonResponse(status: Int, body: JSONObject): String {
        val payload = body.toString()

        val statusText = when (status) {
            200 -> "OK"
            400 -> "Bad Request"
            404 -> "Not Found"
            else -> "Error"
        }

        return buildString {
            append("HTTP/1.1 $status $statusText\r\n")
            append("Content-Type: application/json\r\n")
            append("Content-Length: ${payload.toByteArray().size}\r\n")
            append("Connection: close\r\n")
            append("\r\n")
            append(payload)
        }
    }
}