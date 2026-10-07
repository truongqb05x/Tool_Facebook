using FPlusClone.Models;
using FPlusClone.Views;
using System.Windows.Input;
using System.Linq;

namespace FPlusClone.ViewModels
{
    public class TabSpamGroupViewModel : BaseTabViewModel
    {
        private bool _isSettingsModalOpen;
        public bool IsSettingsModalOpen
        {
            get => _isSettingsModalOpen;
            set { if (_isSettingsModalOpen != value) { _isSettingsModalOpen = value; OnPropertyChanged(); } }
        }

        private int _maxThreads = 3;
        public int MaxThreads
        {
            get => _maxThreads;
            set { if (_maxThreads != value) { _maxThreads = value; OnPropertyChanged(); } }
        }

        private string _logText = "";
        public string LogText
        {
            get => _logText;
            set { if (_logText != value) { _logText = value; OnPropertyChanged(); } }
        }

        public System.Collections.ObjectModel.ObservableCollection<CustomGroupCommentModel> CustomGroupCommentsList { get; set; }
            = new System.Collections.ObjectModel.ObservableCollection<CustomGroupCommentModel>();

        public ICommand AddCustomGroupCommentCommand { get; }
        public ICommand EditCustomGroupCommentCommand { get; }
        public ICommand DeleteCustomGroupCommentCommand { get; }

        private int _maxComments = 5;
        public int MaxComments
        {
            get => _maxComments;
            set { if (_maxComments != value) { _maxComments = value; OnPropertyChanged(); } }
        }

        private int _delayMin = 15;
        public int DelayMin
        {
            get => _delayMin;
            set { if (_delayMin != value) { _delayMin = value; OnPropertyChanged(); } }
        }

        private int _delayMax = 30;
        public int DelayMax
        {
            get => _delayMax;
            set { if (_delayMax != value) { _delayMax = value; OnPropertyChanged(); } }
        }

        private int _delayAccountMin = 5;
        public int DelayAccountMin
        {
            get => _delayAccountMin;
            set { if (_delayAccountMin != value) { _delayAccountMin = value; OnPropertyChanged(); } }
        }

        private int _delayAccountMax = 10;
        public int DelayAccountMax
        {
            get => _delayAccountMax;
            set { if (_delayAccountMax != value) { _delayAccountMax = value; OnPropertyChanged(); } }
        }

        private bool _editAfterPost = true;
        public bool EditAfterPost
        {
            get => _editAfterPost;
            set { if (_editAfterPost != value) { _editAfterPost = value; OnPropertyChanged(); } }
        }

        private bool _isCheckApproval;
        public bool IsCheckApproval
        {
            get => _isCheckApproval;
            set { if (_isCheckApproval != value) { _isCheckApproval = value; OnPropertyChanged(); } }
        }

        private bool _isResetDcom;
        public bool IsResetDcom
        {
            get => _isResetDcom;
            set { if (_isResetDcom != value) { _isResetDcom = value; OnPropertyChanged(); } }
        }

        private int _resetDcomAfter = 2;
        public int ResetDcomAfter
        {
            get => _resetDcomAfter;
            set { if (_resetDcomAfter != value) { _resetDcomAfter = value; OnPropertyChanged(); } }
        }

        public ICommand StartTaskCommand { get; }
        public ICommand StopTaskCommand { get; }
        public ICommand OpenSettingsCommand { get; }
        public ICommand CloseSettingsCommand { get; }

        private readonly string customGroupCommentsFilePath = "custom_group_comments_spamgroup.txt";

        public TabSpamGroupViewModel()
        {
            LoadCustomGroupComments();
            LoadUIConfig();

            StartTaskCommand = new RelayCommand(_ => StartTask());
            StopTaskCommand = new RelayCommand(_ => StopTask());
            OpenSettingsCommand = new RelayCommand(_ => IsSettingsModalOpen = true);
            CloseSettingsCommand = new RelayCommand(_ => IsSettingsModalOpen = false);

            AddCustomGroupCommentCommand = new RelayCommand(_ =>
            {
                var window = new EditCustomGroupCommentWindow()
                {
                    Owner = System.Windows.Application.Current.MainWindow
                };

                if (window.ShowDialog() == true)
                {
                    CustomGroupCommentsList.Add(new CustomGroupCommentModel
                    {
                        GroupId = window.GroupId,
                        Content = window.CommentContent,
                        CommentType = window.CommentType,
                        ImagePath = window.ImagePath
                    });
                    SaveCustomGroupComments();
                }
            });

            DeleteCustomGroupCommentCommand = new RelayCommand(obj =>
            {
                if (obj is CustomGroupCommentModel comment)
                {
                    CustomGroupCommentsList.Remove(comment);
                    SaveCustomGroupComments();
                }
            });

            EditCustomGroupCommentCommand = new RelayCommand(obj =>
            {
                if (obj is CustomGroupCommentModel oldComment)
                {
                    var window = new EditCustomGroupCommentWindow(
                        oldComment.GroupId,
                        oldComment.Content,
                        oldComment.CommentType,
                        oldComment.ImagePath)
                    {
                        Owner = System.Windows.Application.Current.MainWindow
                    };

                    if (window.ShowDialog() == true)
                    {
                        oldComment.GroupId = window.GroupId;
                        oldComment.Content = window.CommentContent;
                        oldComment.CommentType = window.CommentType;
                        oldComment.ImagePath = window.ImagePath;
                        SaveCustomGroupComments();
                    }
                }
            });
        }

        private void SaveUIConfig()
        {
            var config = new System.Collections.Generic.Dictionary<string, object>
            {
                { "MaxThreads", MaxThreads },
                { "MaxComments", MaxComments },
                { "EditAfterPost", EditAfterPost },
                { "IsRepeat", IsRepeat },
                { "RepeatCount", RepeatCount },
                { "ActionBeforePost", ActionBeforePost },
                { "ConfigBeforePost", ConfigBeforePost },
                { "ActionAfterPost", ActionAfterPost },
                { "ConfigAfterPost", ConfigAfterPost },
                { "DelayAccountMin", DelayAccountMin },
                { "DelayAccountMax", DelayAccountMax },
                { "IsResetDcom", IsResetDcom },
                { "ResetDcomAfter", ResetDcomAfter },
                { "IsCheckApproval", IsCheckApproval }
            };
            string json = System.Text.Json.JsonSerializer.Serialize(config);
            System.IO.File.WriteAllText("spam_group_ui_settings.json", json);
        }

        private void LoadUIConfig()
        {
            try
            {
                if (System.IO.File.Exists("spam_group_ui_settings.json"))
                {
                    string json = System.IO.File.ReadAllText("spam_group_ui_settings.json");
                    var config = System.Text.Json.JsonSerializer.Deserialize<System.Collections.Generic.Dictionary<string, System.Text.Json.JsonElement>>(json);
                    if (config != null)
                    {
                        if (config.TryGetValue("MaxThreads", out var v)) MaxThreads = v.GetInt32();
                        if (config.TryGetValue("MaxComments", out v)) MaxComments = v.GetInt32();
                        if (config.TryGetValue("EditAfterPost", out v)) EditAfterPost = v.GetBoolean();
                        if (config.TryGetValue("IsRepeat", out v)) IsRepeat = v.GetBoolean();
                        if (config.TryGetValue("RepeatCount", out v)) RepeatCount = v.GetInt32();
                        if (config.TryGetValue("ActionBeforePost", out v)) ActionBeforePost = v.GetBoolean();
                        if (config.TryGetValue("ConfigBeforePost", out v)) ConfigBeforePost = System.Text.Json.JsonSerializer.Deserialize<FPlusClone.Models.ActionConfig>(v.GetRawText());
                        if (config.TryGetValue("ActionAfterPost", out v)) ActionAfterPost = v.GetBoolean();
                        if (config.TryGetValue("ConfigAfterPost", out v)) ConfigAfterPost = System.Text.Json.JsonSerializer.Deserialize<FPlusClone.Models.ActionConfig>(v.GetRawText());
                        if (config.TryGetValue("DelayAccountMin", out v)) DelayAccountMin = v.GetInt32();
                        if (config.TryGetValue("DelayAccountMax", out v)) DelayAccountMax = v.GetInt32();
                        if (config.TryGetValue("IsResetDcom", out v)) IsResetDcom = v.GetBoolean();
                        if (config.TryGetValue("ResetDcomAfter", out v)) ResetDcomAfter = v.GetInt32();
                        if (config.TryGetValue("IsCheckApproval", out v)) IsCheckApproval = v.GetBoolean();
                    }
                }
            }
            catch { }
        }

        private void LoadCustomGroupComments()
        {
            if (System.IO.File.Exists(customGroupCommentsFilePath))
            {
                var lines = System.IO.File.ReadAllLines(customGroupCommentsFilePath);
                foreach (var line in lines)
                {
                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        // Format: groupId|commentType|imagePath|content
                        var parts = line.Split(new[] { '|' }, 4);
                        string groupId = parts[0];
                        string commentType = parts.Length > 1 ? parts[1] : "Text";
                        string imagePath = parts.Length > 2 ? parts[2] : "";
                        string content = parts.Length > 3 ? parts[3].Replace("[NEWLINE]", "\n") : "";

                        // Backward compat: nếu commentType không phải "Text"/"Image" thì coi là content (format cũ)
                        if (commentType != "Text" && commentType != "Image")
                        {
                            content = (commentType + (imagePath.Length > 0 ? "|" + imagePath : "") + (content.Length > 0 ? "|" + content : "")).Replace("[NEWLINE]", "\n");
                            commentType = "Text";
                            imagePath = "";
                        }

                        CustomGroupCommentsList.Add(new CustomGroupCommentModel
                        {
                            GroupId = groupId,
                            CommentType = commentType,
                            ImagePath = imagePath,
                            Content = content
                        });
                    }
                }
            }
        }

        private void SaveCustomGroupComments()
        {
            // Format: groupId|commentType|imagePath|content
            var lines = CustomGroupCommentsList.Select(c =>
                $"{c.GroupId}|{c.CommentType}|{c.ImagePath ?? ""}|{c.Content?.Replace("\r", "")?.Replace("\n", "[NEWLINE]")}"
            ).ToArray();
            System.IO.File.WriteAllLines(customGroupCommentsFilePath, lines);
        }

        private bool _isRunning;
        public bool IsRunning
        {
            get => _isRunning;
            set { if (_isRunning != value) { _isRunning = value; OnPropertyChanged(); System.Windows.Application.Current.Dispatcher.Invoke(() => System.Windows.Input.CommandManager.InvalidateRequerySuggested()); } }
        }

        private string _statusText;
        public string StatusText
        {
            get => _statusText;
            set { if (_statusText != value) { _statusText = value; OnPropertyChanged(); } }
        }

        private System.Diagnostics.Process _runningProcess;

        private void StartTask()
        {
            if (IsRunning) return;
            SaveUIConfig();

            var selectedTaskAccounts = TaskAccounts.Where(t => t.IsSelected).ToList();
            if (selectedTaskAccounts.Count == 0)
            {
                System.Windows.MessageBox.Show("Vui lòng chọn ít nhất 1 tài khoản để chạy.");
                return;
            }

            var selectedUids = selectedTaskAccounts.Select(t => t.Account.Uid).ToList();
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
                MaxCommentsPerAcc = MaxComments,
                EditAfterPost = EditAfterPost,
                CustomGroupCommentsList = CustomGroupCommentsList.Select(c => new
                {
                    c.GroupId,
                    c.CommentType,
                    c.ImagePath,
                    c.Content
                }).ToList(),
                SelectedAccounts = selectedUids,
                SelectedAccountsInfo = accountLines,

                // Base Tab config
                IsRepeat = IsRepeat,
                RepeatCount = RepeatCount,
                ActionBeforePost = ActionBeforePost,
                ConfigBeforePost = ConfigBeforePost,
                ActionAfterPost = ActionAfterPost,
                ConfigAfterPost = ConfigAfterPost,
                DelayMin = DelayMin,
                DelayMax = DelayMax,
                DelayAccountMin = DelayAccountMin,
                DelayAccountMax = DelayAccountMax,

                // Proxy
                ProxyMethod = appSettings.ProxyMethod,
                ProxyList = proxyLines,
                KiotProxyKey = appSettings.KiotProxyKey ?? "",
                ProfilePath = appSettings.ProfilePath ?? "",

                // Reset DCOM
                IsResetDcom = IsResetDcom,
                ResetDcomAfter = ResetDcomAfter
            };

            string jsonConfig = System.Text.Json.JsonSerializer.Serialize(fullConfig);

            foreach (var acc in selectedTaskAccounts)
                acc.Progress = $"0/{MaxComments}";

            IsRunning = true;
            StatusText = "Đang chạy";
            LogText = "";

            try
            {
                _runningProcess = new System.Diagnostics.Process();

                string baseDir = System.AppDomain.CurrentDomain.BaseDirectory;
                string mainPyPath = System.IO.Path.Combine(baseDir, "Logic", "main.py");
                if (!System.IO.File.Exists(mainPyPath) && baseDir.Contains("bin"))
                {
                    baseDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(baseDir, "..", "..", ".."));
                }

                string configPath = System.IO.Path.Combine(baseDir, "spam_group_config.json");
                System.IO.File.WriteAllText(configPath, jsonConfig);

                _runningProcess.StartInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"-u Logic\\main.py 1 spam_group_config.json",
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
                                LogText = LogText.Substring(LogText.Length - 5000);

                            // UI_STATUS|Die
                            var match = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_STATUS\|Die");
                            if (match.Success)
                            {
                                string uidStr = match.Groups[1].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null)
                                {
                                    acc.Status = "Die";
                                    var mainVm = System.Windows.Application.Current.MainWindow?.DataContext as MainViewModel;
                                    mainVm?.UpdateAccountStatus(uidStr, "Die");
                                }
                            }

                            // UI_PROGRESS_SUCCESS
                            var progressMatch = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_PROGRESS_SUCCESS");
                            if (progressMatch.Success)
                            {
                                string uidStr = progressMatch.Groups[1].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null)
                                {
                                    var parts = acc.Progress.Split('/');
                                    if (parts.Length > 0 && int.TryParse(parts[0], out int currentSuccess))
                                        acc.Progress = $"{currentSuccess + 1}/{MaxComments}";
                                }
                            }

                            // UI_LOGIN_FAILED
                            var loginFailMatch = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_LOGIN_FAILED");
                            if (loginFailMatch.Success)
                            {
                                string uidStr = loginFailMatch.Groups[1].Value.Trim();
                                var mainVm = System.Windows.Application.Current.MainWindow?.DataContext as MainViewModel;
                                mainVm?.UpdateAccountNote(uidStr, "Login Failed");
                            }

                            // UI_REMOVE
                            var removeMatch = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_REMOVE\|(.+)");
                            if (removeMatch.Success)
                            {
                                string uidStr = removeMatch.Groups[2].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null)
                                {
                                    TaskAccounts.Remove(acc);
                                    var mainVm = System.Windows.Application.Current.MainWindow?.DataContext as MainViewModel;
                                    mainVm?.UpdateAccountNote(uidStr, "Pending comment");
                                }
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
                                LogText = LogText.Substring(LogText.Length - 5000);
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
                            System.Windows.MessageBox.Show("Hoành thành!", "Hoàn thành", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
                        }
                        else
                        {
                            StatusText = "Đã dừng";
                        }

                        if (!string.IsNullOrWhiteSpace(errorOutput))
                            System.Windows.MessageBox.Show("Python Error:\n" + errorOutput);
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

        private void StopTask()
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
        }
    }
}
