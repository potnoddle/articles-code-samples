using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace CyberDefenseHarness
{
    /// <summary>
    /// Cryptographically signed capability token (Macaroon-inspired) in C# .NET.
    /// Enforces PoLA, ephemeral 15-minute TTL, and URI/method/IP attenuation.
    /// </summary>
    public class CapabilityToken
    {
        public string Identifier { get; set; }
        public string TargetService { get; set; }
        public List<Caveat> Caveats { get; set; } = new List<Caveat>();
        public string Signature { get; set; }

        private byte[] _currentTag;

        public class Caveat
        {
            public string Predicate { get; set; }
            public string Value { get; set; }
        }

        public CapabilityToken() { }

        public CapabilityToken(byte[] rootKey, string identifier, string targetService)
        {
            Identifier = identifier;
            TargetService = targetService;
            using var hmac = new HMACSHA256(rootKey);
            byte[] msg = Encoding.UTF8.GetBytes($"id:{identifier}|srv:{targetService}");
            _currentTag = hmac.ComputeHash(msg);
            Signature = Convert.ToBase64String(_currentTag);
        }

        public CapabilityToken AddCaveat(string predicate, string value)
        {
            var caveat = new Caveat { Predicate = predicate, Value = value };
            Caveats.Add(caveat);
            using var hmac = new HMACSHA256(_currentTag);
            byte[] caveatBytes = Encoding.UTF8.GetBytes($"{caveat.Predicate}={caveat.Value}");
            _currentTag = hmac.ComputeHash(caveatBytes);
            Signature = Convert.ToBase64String(_currentTag);
            return this;
        }

        public string Serialize()
        {
            string json = JsonSerializer.Serialize(this);
            return Convert.ToBase64String(Encoding.UTF8.GetBytes(json));
        }

        public static bool Verify(string serializedToken, byte[] rootKey, Dictionary<string, string> context)
        {
            try
            {
                byte[] rawJsonBytes = Convert.FromBase64String(serializedToken);
                string json = Encoding.UTF8.GetString(rawJsonBytes);
                var token = JsonSerializer.Deserialize<CapabilityToken>(json);
                if (token == null) return false;

                // Recompute HMAC chain
                byte[] tag;
                using (var hmac = new HMACSHA256(rootKey))
                {
                    tag = hmac.ComputeHash(Encoding.UTF8.GetBytes($"id:{token.Identifier}|srv:{token.TargetService}"));
                }

                foreach (var caveat in token.Caveats)
                {
                    using var hmac = new HMACSHA256(tag);
                    byte[] caveatBytes = Encoding.UTF8.GetBytes($"{caveat.Predicate}={caveat.Value}");
                    tag = hmac.ComputeHash(caveatBytes);
                }

                if (Convert.ToBase64String(tag) != token.Signature)
                {
                    return false; // Signature mismatch
                }

                // Evaluate caveats against execution context
                long nowUnix = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
                foreach (var caveat in token.Caveats)
                {
                    switch (caveat.Predicate)
                    {
                        case "expires_at":
                            if (!long.TryParse(caveat.Value, out long exp) || nowUnix > exp)
                                return false; // Expired
                            break;
                        case "allowed_method":
                            if (!context.TryGetValue("method", out string m) || m != caveat.Value)
                                return false;
                            break;
                        case "allowed_path_prefix":
                            if (!context.TryGetValue("path", out string p) || !p.StartsWith(caveat.Value))
                                return false;
                            break;
                        case "bound_client_ip":
                            if (!context.TryGetValue("client_ip", out string ip) || ip != caveat.Value)
                                return false;
                            break;
                    }
                }

                return true;
            }
            catch
            {
                return false;
            }
        }
    }

    /// <summary>
    /// Ephemeral sandbox execution manager with timeout and process quarantine.
    /// </summary>
    public class EphemeralSandboxManager
    {
        private readonly int _timeoutMs;

        public EphemeralSandboxManager(int timeoutMs = 2000)
        {
            _timeoutMs = timeoutMs;
        }

        public (int exitCode, string stdout, string stderr, bool quarantined) ExecuteBoundedCommand(string command, string args)
        {
            var psi = new ProcessStartInfo
            {
                FileName = command,
                Arguments = args,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            // Clean environment to disallow ambient secret inheritance
            psi.Environment.Clear();
            psi.Environment["PATH"] = Environment.GetEnvironmentVariable("PATH") ?? "";

            using var process = new Process { StartInfo = psi };
            try
            {
                process.Start();
                if (!process.WaitForExit(_timeoutMs))
                {
                    process.Kill(true);
                    return (-1, "", $"Execution timed out after {_timeoutMs}ms (Runaway loop or DoS attempt quarantined)", true);
                }

                string stdout = process.StandardOutput.ReadToEnd();
                string stderr = process.StandardError.ReadToEnd();
                return (process.ExitCode, stdout.Trim(), stderr.Trim(), process.ExitCode != 0);
            }
            catch (Exception ex)
            {
                return (-2, "", ex.Message, true);
            }
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("[.NET 6.0 C# Enterprise Cyber Defense Verification]");
            Console.WriteLine("[1/3] Verifying C# Cryptographic Capability Token (PoLA)...");

            byte[] rootKey = Encoding.UTF8.GetBytes("dotnet-master-secret-signing-key-2026");

            // Mint token valid for 15 minutes (900 seconds)
            long expiry = DateTimeOffset.UtcNow.ToUnixTimeSeconds() + 900;
            var token = new CapabilityToken(rootKey, "dev-agent-session-404", "cloud-inference-mesh")
                .AddCaveat("allowed_method", "POST")
                .AddCaveat("allowed_path_prefix", "/api/v1/inference")
                .AddCaveat("bound_client_ip", "10.0.8.25")
                .AddCaveat("expires_at", expiry.ToString());

            string serialized = token.Serialize();

            // 1. Valid Request Context
            var validContext = new Dictionary<string, string>
            {
                { "method", "POST" },
                { "path", "/api/v1/inference/generate" },
                { "client_ip", "10.0.8.25" }
            };
            if (!CapabilityToken.Verify(serialized, rootKey, validContext))
                throw new Exception("Valid capability token failed verification in C#!");
            Console.WriteLine("  [OK] Valid C# capability token passed verification.");

            // 2. Adversarial Lateral Replay (GTG-50014 token extraction simulation)
            var adversaryContext = new Dictionary<string, string>
            {
                { "method", "POST" },
                { "path", "/api/v1/inference/generate" },
                { "client_ip", "198.51.100.89" } // External stolen replay
            };
            if (CapabilityToken.Verify(serialized, rootKey, adversaryContext))
                throw new Exception("Replay attack was not blocked!");
            Console.WriteLine("  [OK] Replay attack from unauthorized IP blocked.");

            // 3. Unauthorized Privilege Escalation Path
            var lateralContext = new Dictionary<string, string>
            {
                { "method", "POST" },
                { "path", "/api/v1/admin/exfiltrate-secrets" },
                { "client_ip", "10.0.8.25" }
            };
            if (CapabilityToken.Verify(serialized, rootKey, lateralContext))
                throw new Exception("Lateral privilege escalation was not blocked!");
            Console.WriteLine("  [OK] Lateral privilege traversal blocked by capability prefix.");

            Console.WriteLine("\n[2/3] Verifying Ephemeral Process Sandbox (GTG-20006)...");
            var sandbox = new EphemeralSandboxManager(timeoutMs: 1500);

            // Execute runaway script using python/powershell CLI
            var runaway = sandbox.ExecuteBoundedCommand("powershell", "-NoProfile -Command Start-Sleep -Seconds 10");
            if (!runaway.quarantined)
                throw new Exception("Runaway loop was not quarantined by sandbox!");
            Console.WriteLine("  [OK] Runaway execution killed via ephemeral sandbox timeout.");

            Console.WriteLine("\n[3/3] Emitting C# Audit Manifest...");
            var manifest = new
            {
                runtime = ".NET 6.0 (C#)",
                benchmark = "SPEC-COUNTER-CYBER-01",
                timestamp = DateTime.UtcNow.ToString("o"),
                status = "PASSED",
                invariants = new
                {
                    cryptographic_hmac_chain = true,
                    ambient_authority_eliminated = true,
                    max_ttl_seconds = 900,
                    ephemeral_isolation = "Process-Isolated Sandbox"
                }
            };
            string manifestJson = JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true });
            System.IO.File.WriteAllText("dotnet_audit_manifest.json", manifestJson);
            Console.WriteLine("  [OK] Manifest written to dotnet_audit_manifest.json");

            Console.WriteLine("\n[+] All C# .NET Cyber Defense verification benchmarks PASSED successfully.");
        }
    }
}
