using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows.Input;
using FPlusClone.Models;

namespace FPlusClone.ViewModels
{
    public class PreviewRow
    {
        public string Col0 { get; set; }
        public string Col1 { get; set; }
        public string Col2 { get; set; }
        public string Col3 { get; set; }
        public string Col4 { get; set; }
        public string Col5 { get; set; }
        public string Col6 { get; set; }
        public string Col7 { get; set; }
        public string Col8 { get; set; }
        public string Col9 { get; set; }
    }

    public class ImportAccountViewModel : ViewModelBase
    {
        private string _rawData;
        public string RawData
        {
            get => _rawData;
            set
            {
                if (SetProperty(ref _rawData, value))
                {
                    UpdatePreview();
                }
            }
        }

        private bool _isSmartMode = true;
        public bool IsSmartMode
        {
            get => _isSmartMode;
            set
            {
                if (SetProperty(ref _isSmartMode, value))
                    UpdatePreview();
            }
        }

        private string _importNote;
        /// <summary>Ghi chú áp dụng cho toàn bộ tài khoản được import lần này.</summary>
        public string ImportNote
        {
            get => _importNote;
            set => SetProperty(ref _importNote, value);
        }

        public ObservableCollection<string> ColumnOptions { get; }
        public ObservableCollection<MappingOption> SelectedMappings { get; }
        public ObservableCollection<PreviewRow> PreviewData { get; }


        public ICommand ImportCommand { get; }
        public ICommand CloseCommand { get; }
        public ICommand GenerateRandomNoteCommand { get; }

        public event Action<List<FacebookAccount>> AccountsImported;
        public event Action RequestClose;

        public ImportAccountViewModel()
        {
            ColumnOptions = new ObservableCollection<string>
            {
                "UID", "Pass", "Cookie", "Token", "Email", "PassEmail", "Mail khôi phục", "2FA", "Note"
            };

            SelectedMappings = new ObservableCollection<MappingOption>();
            var initialValues = new[] { "UID", "Pass", "Cookie", "Token", "Email", "PassEmail", "Mail khôi phục", "2FA", "Note" };
            foreach (var val in initialValues)
            {
                var opt = new MappingOption { SelectedValue = val };
                opt.PropertyChanged += (s, e) => UpdatePreview();
                SelectedMappings.Add(opt);
            }

            PreviewData = new ObservableCollection<PreviewRow>();

            ImportCommand = new RelayCommand(_ => ExecuteImport());
            CloseCommand = new RelayCommand(_ => RequestClose?.Invoke());
            GenerateRandomNoteCommand = new RelayCommand(_ => ImportNote = GenerateRandomNote());
        }

        private static readonly Random _rng = new Random();
        private string GenerateRandomNote()
        {
            const string chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
            var suffix = new string(Enumerable.Range(0, 6).Select(_ => chars[_rng.Next(chars.Length)]).ToArray());
            return $"Batch_{DateTime.Now:yyyyMMdd}_{suffix}";
        }


        private void UpdatePreview()
        {
            PreviewData.Clear();
            if (string.IsNullOrWhiteSpace(RawData)) return;

            var lines = RawData.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.RemoveEmptyEntries);

            foreach (var line in lines)
            {
                var parts = line.Split('|');
                if (parts.Length == 1) parts = line.Split('\t');

                var row = new PreviewRow();

                if (IsSmartMode)
                {
                    var acc = ParseSmart(line);
                    row.Col0 = acc.Uid;
                    row.Col1 = acc.Password;
                    row.Col2 = acc.Cookie;
                    row.Col3 = acc.Token;
                    row.Col4 = acc.Email;
                    row.Col5 = acc.PassEmail;
                    row.Col6 = acc.RecoveryEmail;
                    row.Col7 = acc.TwoFA;
                    row.Col8 = acc.Note;
                }
                else
                {
                    if (parts.Length > 0) row.Col0 = parts[0].Trim();
                    if (parts.Length > 1) row.Col1 = parts[1].Trim();
                    if (parts.Length > 2) row.Col2 = parts[2].Trim();
                    if (parts.Length > 3) row.Col3 = parts[3].Trim();
                    if (parts.Length > 4) row.Col4 = parts[4].Trim();
                    if (parts.Length > 5) row.Col5 = parts[5].Trim();
                    if (parts.Length > 6) row.Col6 = parts[6].Trim();
                    if (parts.Length > 7) row.Col7 = parts[7].Trim();
                    if (parts.Length > 8) row.Col8 = parts[8].Trim();
                    if (parts.Length > 9) row.Col9 = parts[9].Trim();
                }
                PreviewData.Add(row);
            }
        }

        private FacebookAccount ParseSmart(string line)
        {
            var acc = new FacebookAccount();
            var parts = line.Split(new[] { '|', '\t' }, StringSplitOptions.None).Select(p => p.Trim()).ToList();
            if (parts.Count == 0) return acc;

            var usedIndices = new HashSet<int>();

            // 1. Identify UID (long numeric)
            for (int i = 0; i < parts.Count; i++)
            {
                if (parts[i].Length >= 10 && parts[i].All(char.IsDigit))
                {
                    acc.Uid = parts[i];
                    acc.UserName = parts[i];
                    usedIndices.Add(i);
                    // Password usually follows UID. 
                    // Improved check: not a cookie, not a token, and if it has '@', it shouldn't look like a real email (no dots after @)
                    if (i + 1 < parts.Count)
                    {
                        string next = parts[i + 1].ToLower();
                        bool isCookie = next.Contains("c_user=") || next.Contains("xs=");
                        bool isToken = next.StartsWith("eaaa") && next.Length > 50;
                        bool isEmail = next.Contains("@") && (next.EndsWith(".com") || next.EndsWith(".net") || next.Contains(".vn"));

                        if (!isCookie && !isToken && !isEmail && next.Length > 0 && next.Length < 100)
                        {
                            acc.Password = parts[i + 1];
                            usedIndices.Add(i + 1);
                        }
                    }

                    break;
                }
            }

            // 2. Identify Email, PassEmail and RecoveryEmail
            for (int i = 0; i < parts.Count; i++)
            {
                if (usedIndices.Contains(i)) continue;
                string p = parts[i].ToLower();
                if (p.Contains("@"))
                {
                    if (p.Contains("@hotmail") || p.Contains("@outlook") || p.Contains("@gmail") || p.Contains("@outmail"))
                    {
                        if (string.IsNullOrEmpty(acc.Email))
                        {
                            acc.Email = parts[i];
                            usedIndices.Add(i);
                            
                            // Check if next part is PassEmail. It should not be an email itself (containing both '@' and '.')
                            if (i + 1 < parts.Count && !usedIndices.Contains(i + 1) && parts[i+1].Length > 0 && parts[i+1].Length < 30)
                            {
                                bool nextIsEmail = parts[i+1].Contains("@") && parts[i+1].Contains(".");
                                if (!nextIsEmail)
                                {
                                    acc.PassEmail = parts[i + 1];
                                    usedIndices.Add(i + 1);
                                }
                            }
                        }
                    }
                    else
                    {
                        // It's a RecoveryEmail only if it looks like an email (has a dot)
                        if (string.IsNullOrEmpty(acc.RecoveryEmail) && p.Contains("."))
                        {
                            acc.RecoveryEmail = parts[i];
                            usedIndices.Add(i);
                        }
                    }
                }
            }

            // 3. Identify Cookie
            for (int i = 0; i < parts.Count; i++)
            {
                if (usedIndices.Contains(i)) continue;
                if (parts[i].Contains("c_user=") || parts[i].Contains("xs="))
                {
                    acc.Cookie = parts[i];
                    usedIndices.Add(i);
                }
            }

            // 4. Identify Token
            for (int i = 0; i < parts.Count; i++)
            {
                if (usedIndices.Contains(i)) continue;
                if (parts[i].StartsWith("EAAA") && parts[i].Length > 50)
                {
                    acc.Token = parts[i];
                    usedIndices.Add(i);
                }
            }

            // Note: Proxy and UserAgent parsing removed.

            // 6. Identify 2FA (heuristic: 16 or 32 chars, alphanumeric, uppercase/digit mostly)
            for (int i = 0; i < parts.Count; i++)
            {
                if (usedIndices.Contains(i)) continue;
                string p = parts[i].Replace(" ", "");
                if ((p.Length == 16 || p.Length == 32) && p.All(c => char.IsLetterOrDigit(c)))
                {
                    acc.TwoFA = p;
                    usedIndices.Add(i);
                }
            }

            return acc;
        }

        private void ExecuteImport()
        {
            if (string.IsNullOrWhiteSpace(RawData)) return;

            var accounts = new List<FacebookAccount>();
            var lines = RawData.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.RemoveEmptyEntries);

            foreach (var line in lines)
            {
                FacebookAccount acc;
                if (IsSmartMode)
                {
                    acc = ParseSmart(line);
                }
                else
                {
                    var parts = line.Split('|');
                    if (parts.Length == 1) parts = line.Split('\t');
                    acc = new FacebookAccount();

                    for (int i = 0; i < parts.Length && i < SelectedMappings.Count; i++)
                    {
                        string mapping = SelectedMappings[i].SelectedValue;
                        string value = parts[i].Trim();

                        switch (mapping)
                        {
                            case "UID": acc.Uid = value; acc.UserName = value; break;
                            case "Pass": acc.Password = value; break;
                            case "Cookie": acc.Cookie = value; break;
                            case "Token": acc.Token = value; break;
                            case "Email": acc.Email = value; break;
                            case "PassEmail": acc.PassEmail = value; break;
                            case "Mail khôi phục": acc.RecoveryEmail = value; break;
                            case "2FA": acc.TwoFA = value; break;
                            case "Note": acc.Note = value; break;
                        }
                    }
                }

                if (!string.IsNullOrEmpty(acc.Uid) || !string.IsNullOrEmpty(acc.UserName))
                {
                    acc.Status = "Live";
                    acc.Folder = "default";
                    // Áp dụng note chung nếu account chưa có note riêng từ data
                    if (string.IsNullOrEmpty(acc.Note) && !string.IsNullOrEmpty(ImportNote))
                        acc.Note = ImportNote;
                    accounts.Add(acc);
                }
            }

            AccountsImported?.Invoke(accounts);
            RequestClose?.Invoke();
        }
    }
}
