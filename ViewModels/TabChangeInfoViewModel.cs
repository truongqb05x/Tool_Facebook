using System.Collections.ObjectModel;
using System.Windows.Input;
using System.Linq;
using Microsoft.Win32;
using System.IO;
using FPlusClone.Views;

namespace FPlusClone.ViewModels
{
    public class TabChangeInfoViewModel : BaseTabViewModel
    {
        private bool _isUpAvatar = false;
        public bool IsUpAvatar
        {
            get => _isUpAvatar;
            set { if (_isUpAvatar != value) { _isUpAvatar = value; OnPropertyChanged(); } }
        }

        private bool _isSkipIfHasAvatar = false;
        public bool IsSkipIfHasAvatar
        {
            get => _isSkipIfHasAvatar;
            set { if (_isSkipIfHasAvatar != value) { _isSkipIfHasAvatar = value; OnPropertyChanged(); } }
        }

        private bool _isChangeName = false;
        public bool IsChangeName
        {
            get => _isChangeName;
            set { if (_isChangeName != value) { _isChangeName = value; OnPropertyChanged(); } }
        }

        private bool _isChangeCityNow = false;
        public bool IsChangeCityNow
        {
            get => _isChangeCityNow;
            set { if (_isChangeCityNow != value) { _isChangeCityNow = value; OnPropertyChanged(); } }
        }

        private bool _isChangeHometown = false;
        public bool IsChangeHometown
        {
            get => _isChangeHometown;
            set { if (_isChangeHometown != value) { _isChangeHometown = value; OnPropertyChanged(); } }
        }

        private bool _isChangeHighSchool = false;
        public bool IsChangeHighSchool
        {
            get => _isChangeHighSchool;
            set { if (_isChangeHighSchool != value) { _isChangeHighSchool = value; OnPropertyChanged(); } }
        }

        private bool _isChangeUniversity = false;
        public bool IsChangeUniversity
        {
            get => _isChangeUniversity;
            set { if (_isChangeUniversity != value) { _isChangeUniversity = value; OnPropertyChanged(); } }
        }

        private bool _isChangeRelationship = false;
        public bool IsChangeRelationship
        {
            get => _isChangeRelationship;
            set { if (_isChangeRelationship != value) { _isChangeRelationship = value; OnPropertyChanged(); } }
        }

        private string _avatarFolderPath = "";
        public string AvatarFolderPath
        {
            get => _avatarFolderPath;
            set { if (_avatarFolderPath != value) { _avatarFolderPath = value; OnPropertyChanged(); } }
        }

        private int _maxThreads = 3;
        public int MaxThreads
        {
            get => _maxThreads;
            set { if (_maxThreads != value) { _maxThreads = value; OnPropertyChanged(); } }
        }

        public ICommand StartTaskCommand { get; }
        public ICommand StopTaskCommand { get; }
        public ICommand SelectAvatarFolderCommand { get; }

        public TabChangeInfoViewModel()
        {
            StartTaskCommand = new RelayCommand(_ => ExecuteStartTask(), _ => !IsRunning);
            StopTaskCommand = new RelayCommand(_ => ExecuteStopTask(), _ => IsRunning);
            SelectAvatarFolderCommand = new RelayCommand(_ => ExecuteSelectAvatarFolder());
        }

        private void ExecuteSelectAvatarFolder()
        {
            var dialog = new Microsoft.Win32.OpenFolderDialog
            {
                Title = "Chọn thư mục chứa ảnh Avatar"
            };
            if (dialog.ShowDialog() == true)
            {
                AvatarFolderPath = dialog.FolderName;
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

            var selectedTaskAccounts = TaskAccounts.Where(t => t.IsSelected).ToList();
            if (selectedTaskAccounts.Count == 0)
            {
                System.Windows.MessageBox.Show("Vui lòng chọn ít nhất một tài khoản!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                return;
            }

            if (IsUpAvatar && string.IsNullOrWhiteSpace(AvatarFolderPath))
            {
                System.Windows.MessageBox.Show("Vui lòng chọn thư mục chứa ảnh Avatar!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
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
                IsUpAvatar = IsUpAvatar,
                IsSkipIfHasAvatar = IsSkipIfHasAvatar,
                AvatarFolderPath = AvatarFolderPath,
                IsChangeName = IsChangeName,
                IsChangeCityNow = IsChangeCityNow,
                IsChangeHometown = IsChangeHometown,
                IsChangeHighSchool = IsChangeHighSchool,
                IsChangeUniversity = IsChangeUniversity,
                IsChangeRelationship = IsChangeRelationship,
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
            Log("Bắt đầu thay đổi thông tin (Change Info)...");
            
            try
            {
                _runningProcess = new System.Diagnostics.Process();
                
                string baseDir = System.AppDomain.CurrentDomain.BaseDirectory;
                string mainPyPath = System.IO.Path.Combine(baseDir, "Logic", "main.py");
                if (!System.IO.File.Exists(mainPyPath) && baseDir.Contains("bin"))
                {
                    baseDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(baseDir, "..", "..", ".."));
                }

                string configPath = System.IO.Path.Combine(baseDir, "change_info_config.json");
                System.IO.File.WriteAllText(configPath, jsonConfig);

                _runningProcess.StartInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"-u Logic\\main.py 10 change_info_config.json",
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
                            if (LogText.Length > 10000) LogText = LogText.Substring(LogText.Length - 5000);
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
                                if (acc != null) acc.Status = "Thành công";
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
                            if (LogText.Length > 10000) LogText = LogText.Substring(LogText.Length - 5000);
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
                            System.Windows.MessageBox.Show("Hoàn thành thay đổi thông tin!", "Thành công", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
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
            Log("Đã dừng tác vụ Change Info.");
        }
    }
}
