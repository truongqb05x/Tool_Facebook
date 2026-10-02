using FPlusClone.Models;
using FPlusClone.Views;
using System.Windows.Input;
using System.Linq;

namespace FPlusClone.ViewModels
{
    public class TabSpamGroupViewModel : BaseTabViewModel
    {
        private string _groupUids;
        public string GroupUids
        {
            get => _groupUids;
            set { if (_groupUids != value) { _groupUids = value; SaveGroupUids(); OnPropertyChanged(); } }
        }

        private string _imageGroupUids;
        public string ImageGroupUids
        {
            get => _imageGroupUids;
            set { if (_imageGroupUids != value) { _imageGroupUids = value; SaveImageGroupUids(); OnPropertyChanged(); } }
        }

        private bool _isSequentialComment = true;
        public bool IsSequentialComment
        {
            get => _isSequentialComment;
            set { if (_isSequentialComment != value) { _isSequentialComment = value; OnPropertyChanged(); } }
        }

        private bool _isRandomComment;
        public bool IsRandomComment
        {
            get => _isRandomComment;
            set { if (_isRandomComment != value) { _isRandomComment = value; OnPropertyChanged(); } }
        }
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

        private bool _isTextComment = true;
        public bool IsTextComment
        {
            get => _isTextComment;
            set { if (_isTextComment != value) { _isTextComment = value; OnPropertyChanged(); } }
        }

        private bool _isImageComment;
        public bool IsImageComment
        {
            get => _isImageComment;
            set { if (_isImageComment != value) { _isImageComment = value; OnPropertyChanged(); } }
        }

        private string _imageFolderPath;
        public string ImageFolderPath
        {
            get => _imageFolderPath;
            set { if (_imageFolderPath != value) { _imageFolderPath = value; OnPropertyChanged(); } }
        }

        private bool _isImageCommentWithText;
        public bool IsImageCommentWithText
        {
            get => _isImageCommentWithText;
            set { 
                if (_isImageCommentWithText != value) { 
                    _isImageCommentWithText = value; 
                    if (value) IsImageCommentAutoGenerate = false;
                    OnPropertyChanged(); 
                } 
            }
        }

        private bool _isImageCommentAutoGenerate;
        public bool IsImageCommentAutoGenerate
        {
            get => _isImageCommentAutoGenerate;
            set { 
                if (_isImageCommentAutoGenerate != value) { 
                    _isImageCommentAutoGenerate = value; 
                    if (value) IsImageCommentWithText = false;
                    OnPropertyChanged(); 
                } 
            }
        }

        public System.Collections.ObjectModel.ObservableCollection<CommentModel> CommentsList { get; set; } = new System.Collections.ObjectModel.ObservableCollection<CommentModel>();

        private string _newComment;
        public string NewComment
        {
            get => _newComment;
            set { if (_newComment != value) { _newComment = value; OnPropertyChanged(); } }
        }

        public System.Collections.ObjectModel.ObservableCollection<CustomGroupCommentModel> CustomGroupCommentsList { get; set; } = new System.Collections.ObjectModel.ObservableCollection<CustomGroupCommentModel>();

        public ICommand AddCommentCommand { get; }
        public ICommand EditCommentCommand { get; }
        public ICommand DeleteCommentCommand { get; }
        
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
        public ICommand SelectImageFolderCommand { get; }
        public ICommand OpenSettingsCommand { get; }
        public ICommand CloseSettingsCommand { get; }

        private readonly string commentsFilePath = "comments_spamgroup.txt";
        private readonly string groupUidsFilePath = "group_uids_spamgroup.txt";
        private readonly string imageGroupUidsFilePath = "image_group_uids_spamgroup.txt";
        private readonly string customGroupCommentsFilePath = "custom_group_comments_spamgroup.txt";

        public TabSpamGroupViewModel()
        {
            LoadComments();
            LoadGroupUids();
            LoadImageGroupUids();
            LoadCustomGroupComments();
            LoadUIConfig();

            SelectImageFolderCommand = new RelayCommand(_ =>
            {
                var dialog = new Microsoft.Win32.OpenFolderDialog
                {
                    Title = "Chọn thư mục chứa ảnh bình luận"
                };

                if (dialog.ShowDialog() == true)
                {
                    ImageFolderPath = dialog.FolderName;
                }
            });

            StartTaskCommand = new RelayCommand(_ => StartTask());
            StopTaskCommand = new RelayCommand(_ => StopTask());
            OpenSettingsCommand = new RelayCommand(_ => IsSettingsModalOpen = true);
            CloseSettingsCommand = new RelayCommand(_ => IsSettingsModalOpen = false);

            AddCommentCommand = new RelayCommand(_ =>
            {
                if (!string.IsNullOrWhiteSpace(NewComment))
                {
                    CommentsList.Add(new CommentModel { Index = CommentsList.Count + 1, Content = NewComment });
                    SaveComments();
                    NewComment = string.Empty;
                }
            });

            DeleteCommentCommand = new RelayCommand(obj =>
            {
                if (obj is CommentModel comment)
                {
                    CommentsList.Remove(comment);
                    for (int i = 0; i < CommentsList.Count; i++)
                    {
                        CommentsList[i].Index = i + 1;
                    }
                    SaveComments();
                }
            });

            EditCommentCommand = new RelayCommand(obj =>
            {
                if (obj is CommentModel oldComment)
                {
                    var window = new Views.EditCommentWindow(oldComment.Content)
                    {
                        Owner = System.Windows.Application.Current.MainWindow
                    };

                    if (window.ShowDialog() == true)
                    {
                        string newText = window.CommentText;
                        if (!string.IsNullOrWhiteSpace(newText) && newText != oldComment.Content)
                        {
                            oldComment.Content = newText;
                            SaveComments();
                        }
                    }
                }
            });

            AddCustomGroupCommentCommand = new RelayCommand(_ =>
            {
                var window = new Views.EditCustomGroupCommentWindow()
                {
                    Owner = System.Windows.Application.Current.MainWindow
                };

                if (window.ShowDialog() == true)
                {
                    CustomGroupCommentsList.Add(new CustomGroupCommentModel { GroupId = window.GroupId, Content = window.CommentContent });
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
                    var window = new Views.EditCustomGroupCommentWindow(oldComment.GroupId, oldComment.Content)
                    {
                        Owner = System.Windows.Application.Current.MainWindow
                    };

                    if (window.ShowDialog() == true)
                    {
                        oldComment.GroupId = window.GroupId;
                        oldComment.Content = window.CommentContent;
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
                { "IsTextComment", IsTextComment },
                { "IsImageComment", IsImageComment },
                { "IsImageCommentWithText", IsImageCommentWithText },
                { "IsImageCommentAutoGenerate", IsImageCommentAutoGenerate },
                { "EditAfterPost", EditAfterPost },
                { "ImageFolderPath", ImageFolderPath },
                { "IsSequentialComment", IsSequentialComment },
                { "IsRandomComment", IsRandomComment },
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
                        if (config.TryGetValue("IsTextComment", out v)) IsTextComment = v.GetBoolean();
                        if (config.TryGetValue("IsImageComment", out v)) IsImageComment = v.GetBoolean();
                        if (config.TryGetValue("IsImageCommentWithText", out v)) IsImageCommentWithText = v.GetBoolean();
                        if (config.TryGetValue("IsImageCommentAutoGenerate", out v)) IsImageCommentAutoGenerate = v.GetBoolean();
                        if (config.TryGetValue("EditAfterPost", out v)) EditAfterPost = v.GetBoolean();
                        if (config.TryGetValue("ImageFolderPath", out v)) ImageFolderPath = v.GetString();
                        if (config.TryGetValue("IsSequentialComment", out v)) IsSequentialComment = v.GetBoolean();
                        if (config.TryGetValue("IsRandomComment", out v)) IsRandomComment = v.GetBoolean();
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

        private void LoadComments()
        {
            if (System.IO.File.Exists(commentsFilePath))
            {
                var lines = System.IO.File.ReadAllLines(commentsFilePath);
                int index = 1;
                foreach (var line in lines)
                {
                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        CommentsList.Add(new CommentModel { Index = index++, Content = line.Replace("[NEWLINE]", "\n") });
                    }
                }
            }
        }

        private void SaveComments()
        {
            var lines = CommentsList.Select(c => c.Content?.Replace("\r", "")?.Replace("\n", "[NEWLINE]")).ToArray();
            System.IO.File.WriteAllLines(commentsFilePath, lines);
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
                        var parts = line.Split(new[] { '|' }, 2);
                        string groupId = parts[0];
                        string content = parts.Length > 1 ? parts[1].Replace("[NEWLINE]", "\n") : "";
                        CustomGroupCommentsList.Add(new CustomGroupCommentModel { GroupId = groupId, Content = content });
                    }
                }
            }
        }

        private void SaveCustomGroupComments()
        {
            var lines = CustomGroupCommentsList.Select(c => $"{c.GroupId}|{c.Content?.Replace("\r", "")?.Replace("\n", "[NEWLINE]")}").ToArray();
            System.IO.File.WriteAllLines(customGroupCommentsFilePath, lines);
        }

        private void LoadGroupUids()
        {
            if (System.IO.File.Exists(groupUidsFilePath))
            {
                _groupUids = System.IO.File.ReadAllText(groupUidsFilePath);
                OnPropertyChanged(nameof(GroupUids));
            }
        }

        private void SaveGroupUids()
        {
            if (_groupUids != null)
            {
                System.IO.File.WriteAllText(groupUidsFilePath, _groupUids);
            }
        }

        private void LoadImageGroupUids()
        {
            if (System.IO.File.Exists(imageGroupUidsFilePath))
            {
                _imageGroupUids = System.IO.File.ReadAllText(imageGroupUidsFilePath);
                OnPropertyChanged(nameof(ImageGroupUids));
            }
        }

        private void SaveImageGroupUids()
        {
            if (_imageGroupUids != null)
            {
                System.IO.File.WriteAllText(imageGroupUidsFilePath, _imageGroupUids);
            }
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

            // Đọc cài đặt proxy từ settings.json
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
                MaxThreads = MaxThreads, // <-- Thêm số luồng
                MaxCommentsPerAcc = MaxComments, // <-- Truyền số lượng comment
                GroupUids = GroupUids?.Split(new[] { '\r', '\n' }, System.StringSplitOptions.RemoveEmptyEntries).ToList() ?? new System.Collections.Generic.List<string>(),
                ImageGroupUids = ImageGroupUids?.Split(new[] { '\r', '\n' }, System.StringSplitOptions.RemoveEmptyEntries).ToList() ?? new System.Collections.Generic.List<string>(),
                IsTextComment = IsTextComment,
                IsImageComment = IsImageComment,
                IsImageCommentWithText = IsImageCommentWithText,
                IsImageCommentAutoGenerate = IsImageCommentAutoGenerate,
                EditAfterPost = EditAfterPost,
                ImageFolderPath = ImageFolderPath,
                IsSequentialComment = IsSequentialComment,
                IsRandomComment = IsRandomComment,
                CommentsList = CommentsList.Select(c => c.Content).ToList(),
                CustomGroupCommentsList = CustomGroupCommentsList.Select(c => new { c.GroupId, c.Content }).ToList(),
                SelectedAccounts = selectedUids,
                SelectedAccountsInfo = accountLines, // <-- Truyền trực tiếp qua json
                
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

                // Proxy từ cài đặt hệ thống (Settings Modal)
                ProxyMethod = appSettings.ProxyMethod,
                ProxyList = proxyLines,
                KiotProxyKey = appSettings.KiotProxyKey ?? "",
                ProfilePath = appSettings.ProfilePath ?? "",

                // Reset DCOM (chỉ áp dụng khi KiotProxy)
                IsResetDcom = IsResetDcom,
                ResetDcomAfter = ResetDcomAfter
            };
            
            string jsonConfig = System.Text.Json.JsonSerializer.Serialize(fullConfig);
            System.IO.File.WriteAllText("spam_group_config.json", jsonConfig);

            foreach (var acc in selectedTaskAccounts)
            {
                acc.Progress = $"0/{MaxComments}";
            }

            foreach (var acc in selectedTaskAccounts)
            {
                if (acc.Progress == null || acc.Progress == "" || acc.Progress == "Đang chạy..." || acc.Progress == "Đang chạy")
                    acc.Progress = "0/1";
            }

            IsRunning = true;
            StatusText = "Đang chạy";
            LogText = ""; // Clear log when starting
            
            try
            {
                _runningProcess = new System.Diagnostics.Process();
                
                // Tìm thư mục gốc chứa thư mục Logic
                string baseDir = System.AppDomain.CurrentDomain.BaseDirectory;
                string mainPyPath = System.IO.Path.Combine(baseDir, "Logic", "main.py");
                if (!System.IO.File.Exists(mainPyPath) && baseDir.Contains("bin"))
                {
                    // Lùi lại 3 cấp nếu đang chạy trong bin\Debug\netX.X (về thư mục main)
                    baseDir = System.IO.Path.GetFullPath(System.IO.Path.Combine(baseDir, "..", "..", ".."));
                }

                // Ghi file json vào thư mục chạy python để python chắc chắn đọc được
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
                            {
                                LogText = LogText.Substring(LogText.Length - 5000);
                            }
                            
                            // Check for UI_STATUS|Die
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

                            // Check for UI_PROGRESS_SUCCESS
                            var progressMatch = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_PROGRESS_SUCCESS");
                            if (progressMatch.Success)
                            {
                                string uidStr = progressMatch.Groups[1].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null)
                                {
                                    var parts = acc.Progress.Split('/');
                                    if (parts.Length > 0 && int.TryParse(parts[0], out int currentSuccess))
                                    {
                                        acc.Progress = $"{currentSuccess + 1}/{MaxComments}";
                                    }
                                }
                            }
                            
                            // Check for UI_LOGIN_FAILED
                            var loginFailMatch = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_LOGIN_FAILED");
                            if (loginFailMatch.Success)
                            {
                                string uidStr = loginFailMatch.Groups[1].Value.Trim();
                                var mainVm = System.Windows.Application.Current.MainWindow?.DataContext as MainViewModel;
                                mainVm?.UpdateAccountNote(uidStr, "Login Failed");
                            }
                            
                            // Check for UI_REMOVE|<uid> — xóa account khỏi list chờ chạy
                            var removeMatch = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_REMOVE\|(.+)");
                            if (removeMatch.Success)
                            {
                                string uidStr = removeMatch.Groups[2].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null)
                                {
                                    TaskAccounts.Remove(acc);
                                    // Cập nhật Note trong danh sách tài khoản gốc
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
                        
                        // Nếu tiến trình tự kết thúc thành công (ExitCode == 0)
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

        private void StopTask()
        {
            if (_runningProcess != null && !_runningProcess.HasExited)
            {
                try
                {
                    _runningProcess.Kill();
                }
                catch { }
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
