using FPlusClone.Models;
using FPlusClone.Views;
using System.Windows.Input;
using System.Linq;
using Microsoft.Win32; // for OpenFileDialog
using System.IO;

namespace FPlusClone.ViewModels
{
    public class TabJoinGroupViewModel : BaseTabViewModel
    {
        private string _groupUids;
        public string GroupUids
        {
            get => _groupUids;
            set { if (_groupUids != value) { _groupUids = value; OnPropertyChanged(); } }
        }

        private int _delayMin = 5;
        public int DelayMin
        {
            get => _delayMin;
            set { if (_delayMin != value) { _delayMin = value; OnPropertyChanged(); } }
        }

        private int _delayMax = 10;
        public int DelayMax
        {
            get => _delayMax;
            set { if (_delayMax != value) { _delayMax = value; OnPropertyChanged(); } }
        }

        private int _maxThreads = 3;
        public int MaxThreads
        {
            get => _maxThreads;
            set { if (_maxThreads != value) { _maxThreads = value; OnPropertyChanged(); } }
        }

        private bool _isResetDcom;
        public bool IsResetDcom
        {
            get => _isResetDcom;
            set { if (_isResetDcom != value) { _isResetDcom = value; OnPropertyChanged(); } }
        }

        private int _resetDcomAfter = 5;
        public int ResetDcomAfter
        {
            get => _resetDcomAfter;
            set { if (_resetDcomAfter != value) { _resetDcomAfter = value; OnPropertyChanged(); } }
        }

        public ICommand LoadGroupIdsCommand { get; }
        public ICommand StartTaskCommand { get; }
        public ICommand StopTaskCommand { get; }

        public TabJoinGroupViewModel()
        {
            LoadGroupIdsCommand = new RelayCommand(_ => ExecuteLoadGroupIds());
            StartTaskCommand = new RelayCommand(_ => ExecuteStartTask(), _ => !IsRunning);
            StopTaskCommand = new RelayCommand(_ => ExecuteStopTask(), _ => IsRunning);
        }

        private void ExecuteLoadGroupIds()
        {
            var dialog = new Microsoft.Win32.OpenFileDialog();
            dialog.Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*";
            if (dialog.ShowDialog() == true)
            {
                GroupUids = File.ReadAllText(dialog.FileName);
            }
        }

        private bool _isRunning = false;
        public bool IsRunning
        {
            get => _isRunning;
            set
            {
                if (_isRunning != value)
                {
                    _isRunning = value;
                    OnPropertyChanged();
                    StatusText = _isRunning ? "Đang chạy" : "Đã dừng";
                }
            }
        }

        private string _statusText = "Đã dừng";
        public string StatusText
        {
            get => _statusText;
            set { if (_statusText != value) { _statusText = value; OnPropertyChanged(); } }
        }

        private string _logText = "";
        public string LogText
        {
            get => _logText;
            set { if (_logText != value) { _logText = value; OnPropertyChanged(); } }
        }

        private void Log(string message)
        {
            LogText += $"[{System.DateTime.Now:HH:mm:ss}] {message}\n";
        }

        private System.Diagnostics.Process _runningProcess;

        private void ExecuteStartTask()
        {
            if (IsRunning) return;

            if (string.IsNullOrWhiteSpace(GroupUids))
            {
                System.Windows.MessageBox.Show("Vui lòng nhập danh sách Group ID!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                return;
            }
            var selectedTaskAccounts = TaskAccounts.Where(t => t.IsSelected).ToList();
            if (selectedTaskAccounts.Count == 0)
            {
                System.Windows.MessageBox.Show("Vui lòng chọn ít nhất một tài khoản!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                return;
            }

            var accountLines = selectedTaskAccounts.Select(t => 
                $"{t.Account.Uid}|{t.Account.Password}|{t.Account.TwoFA}|{t.Account.Cookie}|{t.Account.Token}"
            ).ToList();

            var appSettings = SettingsViewModel.Load();
            var proxyLines = new System.Collections.Generic.List<string>();
            if (appSettings.ProxyList != null)
            {
                proxyLines = appSettings.ProxyList
                    .Split(new[] { '\r', '\n' }, System.StringSplitOptions.RemoveEmptyEntries)
                    .Where(l => !string.IsNullOrWhiteSpace(l))
                    .ToList();
            }

            var fullConfig = new
            {
                MaxThreads = MaxThreads,
                DelayAccountMin = DelayMin,
                DelayAccountMax = DelayMax,
                GroupUids = GroupUids?.Split(new[] { '\r', '\n' }, System.StringSplitOptions.RemoveEmptyEntries).ToList() ?? new System.Collections.Generic.List<string>(),
                SelectedAccountsInfo = accountLines,
                IsResetDcom = IsResetDcom,
                ResetDcomAfter = ResetDcomAfter,
                
                ProxyMethod = appSettings.ProxyMethod,
                ProxyList = proxyLines,
                KiotProxyKey = appSettings.KiotProxyKey ?? "",
                ProfilePath = appSettings.ProfilePath ?? "",
            };

            string jsonConfig = System.Text.Json.JsonSerializer.Serialize(fullConfig);

            foreach (var acc in selectedTaskAccounts)
            {
                if (acc.Progress == null || acc.Progress == "" || acc.Progress == "Đang chạy..." || acc.Progress == "Đang chạy")
                    acc.Progress = "0/1";
            }

            IsRunning = true;
            StatusText = "Đang chạy";
            LogText = "";
            Log("Bắt đầu tham gia nhóm...");
            
            try
            {
                _runningProcess = new System.Diagnostics.Process();
                
                string baseDir = System.AppDomain.CurrentDomain.BaseDirectory;
                string mainPyPath = System.IO.Path.Combine(baseDir, "Logic", "main.py");
                if (!System.IO.File.Exists(mainPyPath) && baseDir.Contains("bin"))
                {
                    baseDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(baseDir, "..", "..", ".."));
                }

                string configPath = System.IO.Path.Combine(baseDir, "join_group_config.json");
                System.IO.File.WriteAllText(configPath, jsonConfig);

                _runningProcess.StartInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"-u Logic\\main.py 5 join_group_config.json",
                    WorkingDirectory = baseDir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    StandardOutputEncoding = System.Text.Encoding.UTF8,
                    StandardErrorEncoding = System.Text.Encoding.UTF8
                };
                _runningProcess.StartInfo.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                
                _runningProcess.EnableRaisingEvents = true;
                
                string errorOutput = "";
                _runningProcess.OutputDataReceived += (s, e) => 
                {
                    if (e.Data != null)
                    {
                        System.Windows.Application.Current.Dispatcher.Invoke(() => 
                        {
                            if (e.Data.Trim() == "UI_CLEAR_LOG")
                            {
                                LogText = "";
                                return;
                            }
                            LogText += e.Data + "\n";
                            if (LogText.Length > 10000)
                            {
                                LogText = LogText.Substring(LogText.Length - 5000);
                            }
                            
                            // Tương tự TabSpamGroup, báo tiến trình
                            var matchDie = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_STATUS\|Die");
                            if (matchDie.Success)
                            {
                                string uidStr = matchDie.Groups[1].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null) acc.Status = "Die";
                            }
                            
                            var matchProgress = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_PROGRESS_SUCCESS");
                            if (matchProgress.Success)
                            {
                                string uidStr = matchProgress.Groups[1].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null) { acc.Status = "Thành công"; acc.Progress = "1/1"; }
                            }
                        });
                    }
                };
                _runningProcess.ErrorDataReceived += (s, e) => 
                { 
                    if (e.Data != null) 
                    {
                        errorOutput += e.Data + "\n";
                        System.Windows.Application.Current.Dispatcher.Invoke(() => 
                        {
                            LogText += "[ERROR] " + e.Data + "\n";
                            if (LogText.Length > 10000)
                            {
                                LogText = LogText.Substring(LogText.Length - 5000);
                            }
                        });
                    }
                };
                
                _runningProcess.Exited += (s, e) => 
                {
                    System.Windows.Application.Current.Dispatcher.Invoke(() => 
                    {
                        IsRunning = false;
                        
                        if (_runningProcess != null && _runningProcess.HasExited && _runningProcess.ExitCode == 0)
                        {
                            StatusText = "Đã kết thúc";
                            System.Windows.MessageBox.Show("Hoàn thành tham gia nhóm!", "Thành công", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
                        }
                        else
                        {
                            StatusText = "Đã dừng";
                        }
                        
                        if (!string.IsNullOrWhiteSpace(errorOutput))
                        {
                            System.Windows.MessageBox.Show("Python Error:\n" + errorOutput);
                        }
                    });
                };
                
                _runningProcess.Start();
                _runningProcess.BeginOutputReadLine();
                _runningProcess.BeginErrorReadLine();
            }
            catch (System.Exception ex)
            {
                IsRunning = false;
                StatusText = "Lỗi";
                System.Windows.MessageBox.Show("Lỗi khởi tạo python: " + ex.Message);
            }
        }

        private void ExecuteStopTask()
        {
            if (_runningProcess != null && !_runningProcess.HasExited)
            {
                try { _runningProcess.Kill(); } catch { }
            }

            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "taskkill",
                    Arguments = "/F /IM chrome.exe /T",
                    CreateNoWindow = true,
                    UseShellExecute = false
                });
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "taskkill",
                    Arguments = "/F /IM chromedriver.exe /T",
                    CreateNoWindow = true,
                    UseShellExecute = false
                });
            }
            catch { }

            IsRunning = false;
            StatusText = "Đã dừng";
            Log("Đã dừng tham gia nhóm.");
        }
    }
}
