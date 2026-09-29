using System.Collections.ObjectModel;
using System.Windows.Input;
using System.Linq;
using Microsoft.Win32;
using System.IO;
using FPlusClone.Views;

namespace FPlusClone.ViewModels
{
    public class TabSpamPageViewModel : BaseTabViewModel
    {
        private string _pageList = "";
        public string PageList
        {
            get => _pageList;
            set { if (_pageList != value) { _pageList = value; OnPropertyChanged(); } }
        }

        private string _commentsText = "";
        public string CommentsText
        {
            get => _commentsText;
            set { if (_commentsText != value) { _commentsText = value; OnPropertyChanged(); } }
        }

        private string _imageFolderPath = "";
        public string ImageFolderPath
        {
            get => _imageFolderPath;
            set { if (_imageFolderPath != value) { _imageFolderPath = value; OnPropertyChanged(); } }
        }

        private bool _isTextComment = true;
        public bool IsTextComment
        {
            get => _isTextComment;
            set { if (_isTextComment != value) { _isTextComment = value; OnPropertyChanged(); } }
        }

        private bool _isImageComment = false;
        public bool IsImageComment
        {
            get => _isImageComment;
            set { if (_isImageComment != value) { _isImageComment = value; OnPropertyChanged(); } }
        }

        private int _maxComments = 3;
        public int MaxComments
        {
            get => _maxComments;
            set { if (_maxComments != value) { _maxComments = value; OnPropertyChanged(); } }
        }

        private int _delayMin = 20;
        public int DelayMin
        {
            get => _delayMin;
            set { if (_delayMin != value) { _delayMin = value; OnPropertyChanged(); } }
        }

        private int _delayMax = 40;
        public int DelayMax
        {
            get => _delayMax;
            set { if (_delayMax != value) { _delayMax = value; OnPropertyChanged(); } }
        }

        private bool _isDeleteAfterComment = true;
        public bool IsDeleteAfterComment
        {
            get => _isDeleteAfterComment;
            set { if (_isDeleteAfterComment != value) { _isDeleteAfterComment = value; OnPropertyChanged(); } }
        }

        private int _maxThreads = 3;
        public int MaxThreads
        {
            get => _maxThreads;
            set { if (_maxThreads != value) { _maxThreads = value; OnPropertyChanged(); } }
        }

        public ICommand StartTaskCommand { get; }
        public ICommand StopTaskCommand { get; }
        public ICommand SelectImageFolderCommand { get; }

        public TabSpamPageViewModel()
        {
            StartTaskCommand = new RelayCommand(_ => ExecuteStartTask(), _ => !IsRunning);
            StopTaskCommand = new RelayCommand(_ => ExecuteStopTask(), _ => IsRunning);
            SelectImageFolderCommand = new RelayCommand(_ => ExecuteSelectImageFolder());
        }

        private void ExecuteSelectImageFolder()
        {
            var dialog = new Microsoft.Win32.OpenFolderDialog
            {
                Title = "Chọn thư mục chứa ảnh"
            };
            if (dialog.ShowDialog() == true)
            {
                ImageFolderPath = dialog.FolderName;
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

            if (string.IsNullOrWhiteSpace(PageList))
            {
                System.Windows.MessageBox.Show("Vui lòng nhập danh sách Page ID!", "Thông báo", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
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
                MaxCommentsPerAcc = MaxComments,
                DelayAccountMin = DelayMin,
                DelayAccountMax = DelayMax,
                PageCommentMode = IsImageComment ? "image" : "text",
                IsDeleteAfterComment = IsDeleteAfterComment,
                ImageFolderPath = ImageFolderPath,
                PageList = PageList?.Split(new[] { '\r', '\n' }, System.StringSplitOptions.RemoveEmptyEntries).ToList() ?? new System.Collections.Generic.List<string>(),
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
            Log("Bắt đầu comment page...");
            
            try
            {
                _runningProcess = new System.Diagnostics.Process();
                
                string baseDir = System.AppDomain.CurrentDomain.BaseDirectory;
                string mainPyPath = System.IO.Path.Combine(baseDir, "Logic", "main.py");
                if (!System.IO.File.Exists(mainPyPath) && baseDir.Contains("bin"))
                {
                    baseDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(baseDir, "..", "..", ".."));
                }

                string configPath = System.IO.Path.Combine(baseDir, "spam_page_config.json");
                System.IO.File.WriteAllText(configPath, jsonConfig);

                string resourcesDir = System.IO.Path.Combine(baseDir, "resources");
                if (!System.IO.Directory.Exists(resourcesDir)) System.IO.Directory.CreateDirectory(resourcesDir);
                string editSttPath = System.IO.Path.Combine(resourcesDir, "edit_stt.txt");
                System.IO.File.WriteAllText(editSttPath, CommentsText ?? "");

                _runningProcess.StartInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"-u Logic\\main.py 8 spam_page_config.json",
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
                            System.Windows.MessageBox.Show("Hoàn thành comment page!", "Thành công", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
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
            Log("Đã dừng comment page.");
        }
    }
}
