using System.Collections.ObjectModel;
using System.Windows.Input;
using System.Linq;
using Microsoft.Win32;
using System.IO;
using FPlusClone.Views;

namespace FPlusClone.ViewModels
{
    public class TabOutGroupViewModel : BaseTabViewModel
    {
        private bool _isOutModeAll = true;
        public bool IsOutModeAll
        {
            get => _isOutModeAll;
            set { if (_isOutModeAll != value) { _isOutModeAll = value; OnPropertyChanged(); } }
        }

        private bool _isOutModeList = false;
        public bool IsOutModeList
        {
            get => _isOutModeList;
            set { if (_isOutModeList != value) { _isOutModeList = value; OnPropertyChanged(); } }
        }

        private bool _isOutModeExceptList = false;
        public bool IsOutModeExceptList
        {
            get => _isOutModeExceptList;
            set { if (_isOutModeExceptList != value) { _isOutModeExceptList = value; OnPropertyChanged(); } }
        }

        // Helper cho Python (0: Tất cả, 1: Theo danh sách, 2: Ngoại trừ danh sách)
        public int OutGroupMode => IsOutModeAll ? 0 : IsOutModeList ? 1 : 2;

        private string _groupUids = "";
        public string GroupUids
        {
            get => _groupUids;
            set { if (_groupUids != value) { _groupUids = value; OnPropertyChanged(); } }
        }

        private int _delayMin = 10;
        public int DelayMin
        {
            get => _delayMin;
            set { if (_delayMin != value) { _delayMin = value; OnPropertyChanged(); } }
        }

        private int _delayMax = 20;
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

        public ICommand LoadGroupIdsCommand { get; }
        public ICommand StartTaskCommand { get; }
        public ICommand StopTaskCommand { get; }

        public TabOutGroupViewModel()
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
                    System.Windows.Application.Current.Dispatcher.Invoke(() => System.Windows.Input.CommandManager.InvalidateRequerySuggested());
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

            if (OutGroupMode == 1 && string.IsNullOrWhiteSpace(GroupUids))
            {
                System.Windows.MessageBox.Show("Vui lòng nhập danh sách Group ID/Link khi chọn chế độ này!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                return;
            }

            if (TaskAccounts.Count == 0)
            {
                System.Windows.MessageBox.Show("Vui lòng chọn ít nhất một tài khoản!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                return;
            }

            var accountLines = TaskAccounts.Select(t => 
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
                OutGroupMode = OutGroupMode,
                GroupUids = GroupUids?.Split(new[] { '\r', '\n' }, System.StringSplitOptions.RemoveEmptyEntries).ToList() ?? new System.Collections.Generic.List<string>(),
                SelectedAccountsInfo = accountLines,
                ProxyMethod = appSettings.ProxyMethod,
                ProxyList = proxyLines,
                KiotProxyKey = appSettings.KiotProxyKey ?? "",
                ProfilePath = appSettings.ProfilePath ?? "",
            };

            string jsonConfig = System.Text.Json.JsonSerializer.Serialize(fullConfig);

            IsRunning = true;
            StatusText = "Đang chạy";
            LogText = "";
            Log("Bắt đầu rời nhóm...");
            
            try
            {
                _runningProcess = new System.Diagnostics.Process();
                
                string baseDir = System.AppDomain.CurrentDomain.BaseDirectory;
                string mainPyPath = System.IO.Path.Combine(baseDir, "Logic", "main.py");
                if (!System.IO.File.Exists(mainPyPath) && baseDir.Contains("bin"))
                {
                    baseDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(baseDir, "..", "..", ".."));
                }

                string configPath = System.IO.Path.Combine(baseDir, "out_group_config.json");
                System.IO.File.WriteAllText(configPath, jsonConfig);

                _runningProcess.StartInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"-u Logic\\main.py 7 out_group_config.json",
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
                            LogText += e.Data + "\n";
                            var matchDie = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_STATUS\|Die");
                            if (matchDie.Success)
                            {
                                string uidStr = matchDie.Groups[1].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null) acc.Status = "Die";
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
                            System.Windows.MessageBox.Show("Hoàn thành rời nhóm!", "Thành công", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
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
            Log("Đã dừng rời nhóm.");
        }
    }
}
