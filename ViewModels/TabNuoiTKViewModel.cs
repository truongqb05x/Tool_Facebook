using FPlusClone.Models;
using FPlusClone.Views;
using System.Windows.Input;
using System.Linq;

namespace FPlusClone.ViewModels
{
    public class TabNuoiTKViewModel : BaseTabViewModel
    {
        private int _feedTime = 3;
        public int FeedTime
        {
            get => _feedTime;
            set { if (_feedTime != value) { _feedTime = value; OnPropertyChanged(); } }
        }

        private bool _isEmotionLike = true;
        public bool IsEmotionLike
        {
            get => _isEmotionLike;
            set { if (_isEmotionLike != value) { _isEmotionLike = value; OnPropertyChanged(); } }
        }

        private bool _isEmotionTym = true;
        public bool IsEmotionTym
        {
            get => _isEmotionTym;
            set { if (_isEmotionTym != value) { _isEmotionTym = value; OnPropertyChanged(); } }
        }

        private bool _isEmotionThuong;
        public bool IsEmotionThuong
        {
            get => _isEmotionThuong;
            set { if (_isEmotionThuong != value) { _isEmotionThuong = value; OnPropertyChanged(); } }
        }

        private bool _isEmotionHaha;
        public bool IsEmotionHaha
        {
            get => _isEmotionHaha;
            set { if (_isEmotionHaha != value) { _isEmotionHaha = value; OnPropertyChanged(); } }
        }

        private bool _isEmotionWow;
        public bool IsEmotionWow
        {
            get => _isEmotionWow;
            set { if (_isEmotionWow != value) { _isEmotionWow = value; OnPropertyChanged(); } }
        }

        private bool _isEmotionBuon;
        public bool IsEmotionBuon
        {
            get => _isEmotionBuon;
            set { if (_isEmotionBuon != value) { _isEmotionBuon = value; OnPropertyChanged(); } }
        }

        private bool _isEmotionPhanNo;
        public bool IsEmotionPhanNo
        {
            get => _isEmotionPhanNo;
            set { if (_isEmotionPhanNo != value) { _isEmotionPhanNo = value; OnPropertyChanged(); } }
        }

        private int _delayMin = 10;
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

        private bool _isReadNoti = true;
        public bool IsReadNoti
        {
            get => _isReadNoti;
            set { if (_isReadNoti != value) { _isReadNoti = value; OnPropertyChanged(); } }
        }

        private int _readNotiCount = 5;
        public int ReadNotiCount
        {
            get => _readNotiCount;
            set { if (_readNotiCount != value) { _readNotiCount = value; OnPropertyChanged(); } }
        }

        private bool _isChat;
        public bool IsChat
        {
            get => _isChat;
            set { if (_isChat != value) { _isChat = value; OnPropertyChanged(); } }
        }

        private bool _isPost;
        public bool IsPost
        {
            get => _isPost;
            set { if (_isPost != value) { _isPost = value; OnPropertyChanged(); } }
        }

        private bool _isRandomClick = true;
        public bool IsRandomClick
        {
            get => _isRandomClick;
            set { if (_isRandomClick != value) { _isRandomClick = value; OnPropertyChanged(); } }
        }

        private bool _isAcceptFriend;
        public bool IsAcceptFriend
        {
            get => _isAcceptFriend;
            set { if (_isAcceptFriend != value) { _isAcceptFriend = value; OnPropertyChanged(); } }
        }

        private int _acceptFriendCount = 5;
        public int AcceptFriendCount
        {
            get => _acceptFriendCount;
            set { if (_acceptFriendCount != value) { _acceptFriendCount = value; OnPropertyChanged(); } }
        }

        private bool _isAddFriendSuggested;
        public bool IsAddFriendSuggested
        {
            get => _isAddFriendSuggested;
            set { if (_isAddFriendSuggested != value) { _isAddFriendSuggested = value; OnPropertyChanged(); } }
        }

        private int _addFriendSuggestedCount = 5;
        public int AddFriendSuggestedCount
        {
            get => _addFriendSuggestedCount;
            set { if (_addFriendSuggestedCount != value) { _addFriendSuggestedCount = value; OnPropertyChanged(); } }
        }

        private bool _isUpStory;
        public bool IsUpStory
        {
            get => _isUpStory;
            set { if (_isUpStory != value) { _isUpStory = value; OnPropertyChanged(); } }
        }

        private string _storyFolderPath = "";
        public string StoryFolderPath
        {
            get => _storyFolderPath;
            set { if (_storyFolderPath != value) { _storyFolderPath = value; OnPropertyChanged(); } }
        }

        private bool _isViewStory;
        public bool IsViewStory
        {
            get => _isViewStory;
            set { if (_isViewStory != value) { _isViewStory = value; OnPropertyChanged(); } }
        }

        // --- Reel Properties ---
        private bool _isWatchReel;
        public bool IsWatchReel
        {
            get => _isWatchReel;
            set { if (_isWatchReel != value) { _isWatchReel = value; OnPropertyChanged(); } }
        }

        private int _reelTimeMin = 15;
        public int ReelTimeMin
        {
            get => _reelTimeMin;
            set { if (_reelTimeMin != value) { _reelTimeMin = value; OnPropertyChanged(); } }
        }

        private int _reelTimeMax = 30;
        public int ReelTimeMax
        {
            get => _reelTimeMax;
            set { if (_reelTimeMax != value) { _reelTimeMax = value; OnPropertyChanged(); } }
        }

        private bool _isReelLike;
        public bool IsReelLike
        {
            get => _isReelLike;
            set { if (_isReelLike != value) { _isReelLike = value; OnPropertyChanged(); } }
        }

        private bool _isReelSave;
        public bool IsReelSave
        {
            get => _isReelSave;
            set { if (_isReelSave != value) { _isReelSave = value; OnPropertyChanged(); } }
        }

        private bool _isReelShare;
        public bool IsReelShare
        {
            get => _isReelShare;
            set { if (_isReelShare != value) { _isReelShare = value; OnPropertyChanged(); } }
        }

        private int _reelDelayMin = 2;
        public int ReelDelayMin
        {
            get => _reelDelayMin;
            set { if (_reelDelayMin != value) { _reelDelayMin = value; OnPropertyChanged(); } }
        }

        private int _reelDelayMax = 5;
        public int ReelDelayMax
        {
            get => _reelDelayMax;
            set { if (_reelDelayMax != value) { _reelDelayMax = value; OnPropertyChanged(); } }
        }


        private int _maxThreads = 1;
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

        private string _logText = "";
        public string LogText
        {
            get => _logText;
            set { if (_logText != value) { _logText = value; OnPropertyChanged(); } }
        }

        private bool _isRunning;
        public bool IsRunning
        {
            get => _isRunning;
            set { if (_isRunning != value) { _isRunning = value; OnPropertyChanged(); System.Windows.Application.Current.Dispatcher.Invoke(() => System.Windows.Input.CommandManager.InvalidateRequerySuggested()); } }
        }

        private string _statusText = "Chưa chạy";
        public string StatusText
        {
            get => _statusText;
            set { if (_statusText != value) { _statusText = value; OnPropertyChanged(); } }
        }

        public ICommand StartTaskCommand { get; }
        public ICommand StopTaskCommand { get; }

        private System.Diagnostics.Process _runningProcess;

        public TabNuoiTKViewModel()
        {
            LoadUIConfig();
            StartTaskCommand = new RelayCommand(_ => StartTask());
            StopTaskCommand = new RelayCommand(_ => StopTask());
        }

        private void SaveUIConfig()
        {
            var config = new System.Collections.Generic.Dictionary<string, object>
            {
                { "FeedTime", FeedTime },
                { "IsEmotionLike", IsEmotionLike },
                { "IsEmotionTym", IsEmotionTym },
                { "IsEmotionThuong", IsEmotionThuong },
                { "IsEmotionHaha", IsEmotionHaha },
                { "IsEmotionWow", IsEmotionWow },
                { "IsEmotionBuon", IsEmotionBuon },
                { "IsEmotionPhanNo", IsEmotionPhanNo },
                { "DelayMin", DelayMin },
                { "DelayMax", DelayMax },
                { "IsReadNoti", IsReadNoti },
                { "ReadNotiCount", ReadNotiCount },
                { "IsChat", IsChat },
                { "IsPost", IsPost },
                { "IsRandomClick", IsRandomClick },
                { "IsAcceptFriend", IsAcceptFriend },
                { "AcceptFriendCount", AcceptFriendCount },
                { "IsAddFriendSuggested", IsAddFriendSuggested },
                { "AddFriendSuggestedCount", AddFriendSuggestedCount },
                { "IsUpStory", IsUpStory },
                { "StoryFolderPath", StoryFolderPath },
                { "IsViewStory", IsViewStory },
                { "IsWatchReel", IsWatchReel },
                { "ReelTimeMin", ReelTimeMin },
                { "ReelTimeMax", ReelTimeMax },
                { "IsReelLike", IsReelLike },
                { "IsReelSave", IsReelSave },
                { "IsReelShare", IsReelShare },
                { "ReelDelayMin", ReelDelayMin },
                { "ReelDelayMax", ReelDelayMax },
                { "MaxThreads", MaxThreads },
                { "IsResetDcom", IsResetDcom },
                { "ResetDcomAfter", ResetDcomAfter }
            };
            string json = System.Text.Json.JsonSerializer.Serialize(config);
            System.IO.File.WriteAllText("nuoitk_ui_settings.json", json);
        }

        private void LoadUIConfig()
        {
            try
            {
                if (System.IO.File.Exists("nuoitk_ui_settings.json"))
                {
                    string json = System.IO.File.ReadAllText("nuoitk_ui_settings.json");
                    var config = System.Text.Json.JsonSerializer.Deserialize<System.Collections.Generic.Dictionary<string, System.Text.Json.JsonElement>>(json);
                    if (config != null)
                    {
                        if (config.TryGetValue("FeedTime", out var v)) FeedTime = v.GetInt32();
                        if (config.TryGetValue("IsEmotionLike", out v)) IsEmotionLike = v.GetBoolean();
                        if (config.TryGetValue("IsEmotionTym", out v)) IsEmotionTym = v.GetBoolean();
                        if (config.TryGetValue("IsEmotionThuong", out v)) IsEmotionThuong = v.GetBoolean();
                        if (config.TryGetValue("IsEmotionHaha", out v)) IsEmotionHaha = v.GetBoolean();
                        if (config.TryGetValue("IsEmotionWow", out v)) IsEmotionWow = v.GetBoolean();
                        if (config.TryGetValue("IsEmotionBuon", out v)) IsEmotionBuon = v.GetBoolean();
                        if (config.TryGetValue("IsEmotionPhanNo", out v)) IsEmotionPhanNo = v.GetBoolean();
                        if (config.TryGetValue("DelayMin", out v)) DelayMin = v.GetInt32();
                        if (config.TryGetValue("DelayMax", out v)) DelayMax = v.GetInt32();
                        if (config.TryGetValue("IsReadNoti", out v)) IsReadNoti = v.GetBoolean();
                        if (config.TryGetValue("ReadNotiCount", out v)) ReadNotiCount = v.GetInt32();
                        if (config.TryGetValue("IsChat", out v)) IsChat = v.GetBoolean();
                        if (config.TryGetValue("IsPost", out v)) IsPost = v.GetBoolean();
                        if (config.TryGetValue("IsRandomClick", out v)) IsRandomClick = v.GetBoolean();
                        if (config.TryGetValue("IsAcceptFriend", out v)) IsAcceptFriend = v.GetBoolean();
                        if (config.TryGetValue("AcceptFriendCount", out v)) AcceptFriendCount = v.GetInt32();
                        if (config.TryGetValue("IsAddFriendSuggested", out v)) IsAddFriendSuggested = v.GetBoolean();
                        if (config.TryGetValue("AddFriendSuggestedCount", out v)) AddFriendSuggestedCount = v.GetInt32();
                        if (config.TryGetValue("IsUpStory", out v)) IsUpStory = v.GetBoolean();
                        if (config.TryGetValue("StoryFolderPath", out v)) StoryFolderPath = v.GetString();
                        if (config.TryGetValue("IsViewStory", out v)) IsViewStory = v.GetBoolean();
                        if (config.TryGetValue("IsWatchReel", out v)) IsWatchReel = v.GetBoolean();
                        if (config.TryGetValue("ReelTimeMin", out v)) ReelTimeMin = v.GetInt32();
                        if (config.TryGetValue("ReelTimeMax", out v)) ReelTimeMax = v.GetInt32();
                        if (config.TryGetValue("IsReelLike", out v)) IsReelLike = v.GetBoolean();
                        if (config.TryGetValue("IsReelSave", out v)) IsReelSave = v.GetBoolean();
                        if (config.TryGetValue("IsReelShare", out v)) IsReelShare = v.GetBoolean();
                        if (config.TryGetValue("ReelDelayMin", out v)) ReelDelayMin = v.GetInt32();
                        if (config.TryGetValue("ReelDelayMax", out v)) ReelDelayMax = v.GetInt32();
                        if (config.TryGetValue("MaxThreads", out v)) MaxThreads = v.GetInt32();
                        if (config.TryGetValue("IsResetDcom", out v)) IsResetDcom = v.GetBoolean();
                        if (config.TryGetValue("ResetDcomAfter", out v)) ResetDcomAfter = v.GetInt32();
                    }
                }
            }
            catch { }
        }

        private void StartTask()
        {
            if (IsRunning) return;
            SaveUIConfig();

            var selectedTaskAccounts = TaskAccounts.Where(t => t.IsSelected).ToList();
            var selectedUids = selectedTaskAccounts.Select(t => t.Account.Uid).ToList();
            if (selectedUids.Count == 0)
            {
                System.Windows.MessageBox.Show("Vui lòng chọn ít nhất 1 tài khoản để chạy.");
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
                FeedTime = FeedTime,
                IsLikePost = IsEmotionLike || IsEmotionTym || IsEmotionThuong || IsEmotionHaha || IsEmotionWow || IsEmotionBuon || IsEmotionPhanNo,
                IsReactionLike = IsEmotionLike,
                IsReactionLove = IsEmotionTym,
                IsReactionCare = IsEmotionThuong,
                IsReactionHaha = IsEmotionHaha,
                IsReactionWow = IsEmotionWow,
                IsReactionSad = IsEmotionBuon,
                IsReactionAngry = IsEmotionPhanNo,
                ReactionDelayMin = DelayMin,
                ReactionDelayMax = DelayMax,
                IsReadNoti = IsReadNoti,
                ReadNotiCount = ReadNotiCount,
                IsChat = IsChat,
                IsPost = IsPost,
                IsRandomClick = IsRandomClick,
                
                IsAcceptFriend = IsAcceptFriend,
                AcceptFriendCount = AcceptFriendCount,
                IsAddFriendSuggested = IsAddFriendSuggested,
                AddFriendSuggestedCount = AddFriendSuggestedCount,
                IsUpStory = IsUpStory,
                StoryFolderPath = StoryFolderPath,
                IsViewStory = IsViewStory,
                
                IsWatchReel = IsWatchReel,
                ReelTimeMin = ReelTimeMin,
                ReelTimeMax = ReelTimeMax,
                IsReelLike = IsReelLike,
                IsReelSave = IsReelSave,
                IsReelShare = IsReelShare,
                ReelDelayMin = ReelDelayMin,
                ReelDelayMax = ReelDelayMax,
                
                IsRepeat = IsRepeat,
                RepeatCount = RepeatCount,
                
                SelectedAccounts = selectedUids,
                SelectedAccountsInfo = accountLines,
                
                ProxyMethod = appSettings.ProxyMethod,
                ProxyList = proxyLines,
                KiotProxyKey = appSettings.KiotProxyKey ?? "",
                ProfilePath = appSettings.ProfilePath ?? "",
                IsResetDcom = IsResetDcom,
                ResetDcomAfter = ResetDcomAfter
            };
            
            string jsonConfig = System.Text.Json.JsonSerializer.Serialize(fullConfig);
            
            foreach (var acc in selectedTaskAccounts)
            {
                acc.Progress = "Đang chạy...";
            }

            foreach (var acc in selectedTaskAccounts)
            {
                if (acc.Progress == null || acc.Progress == "" || acc.Progress == "Đang chạy..." || acc.Progress == "Đang chạy")
                    acc.Progress = "0/1";
            }

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

                string configPath = System.IO.Path.Combine(baseDir, "nuoitk_config.json");
                System.IO.File.WriteAllText(configPath, jsonConfig);

                _runningProcess.StartInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"-u Logic\\main.py 3 nuoitk_config.json", // Mode 3 is Warmup
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
                                    acc.Progress = "Nuôi tài khoản hoàn tất";
                                }
                            }

                            // Check for UI_POST_SUCCESS — đăng bài thành công
                            var postSuccessMatch = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_POST_SUCCESS");
                            if (postSuccessMatch.Success)
                            {
                                string uidStr = postSuccessMatch.Groups[1].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null)
                                {
                                    acc.Progress = $"✅ Đã đăng bài ({System.DateTime.Now:dd/MM HH:mm})";
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
                            
                            var removeMatch = System.Text.RegularExpressions.Regex.Match(e.Data, @"\[(.*?)\]\s*UI_REMOVE\|(.+)");
                            if (removeMatch.Success)
                            {
                                string uidStr = removeMatch.Groups[2].Value.Trim();
                                var acc = TaskAccounts.FirstOrDefault(a => a.Account.Uid == uidStr);
                                if (acc != null)
                                {
                                    TaskAccounts.Remove(acc);
                                    var mainVm = System.Windows.Application.Current.MainWindow?.DataContext as MainViewModel;
                                    mainVm?.UpdateAccountNote(uidStr, "Pending (bị từ chối/chờ duyệt)");
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
                            System.Windows.MessageBox.Show("Hoàn thành công việc!", "Hoàn thành", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
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
