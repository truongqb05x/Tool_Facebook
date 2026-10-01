using FPlusClone.Models;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows;
using System.Windows.Input;

namespace FPlusClone.Views
{
    public partial class SelectAccountWindow : Window
    {
        public ObservableCollection<FacebookAccount> Accounts { get; set; }
        public System.Windows.Data.ListCollectionView ItemsView { get; set; }
        public ObservableCollection<string> Folders { get; set; }
        
        private string _selectedFolder;
        public string SelectedFolder
        {
            get => _selectedFolder;
            set
            {
                if (_selectedFolder != value)
                {
                    _selectedFolder = value;
                    ItemsView.Refresh();
                }
            }
        }

        private string _searchUid;
        public string SearchUid
        {
            get => _searchUid;
            set
            {
                if (_searchUid != value)
                {
                    _searchUid = value;
                    ItemsView.Refresh();
                }
            }
        }

        public ObservableCollection<FacebookAccount> SelectedAccountsResult { get; private set; }

        public ICommand SelectAllCommand { get; }
        public ICommand SelectHighlightedCommand { get; }

        public SelectAccountWindow(ObservableCollection<FacebookAccount> globalAccounts)
        {
            InitializeComponent();
            
            Accounts = new ObservableCollection<FacebookAccount>(
                globalAccounts.Select(a => new FacebookAccount 
                { 
                    Uid = a.Uid, 
                    Name = a.Name, 
                    Cookie = a.Cookie, 
                    Token = a.Token,
                    Folder = a.Folder,
                    Password = a.Password,
                    Note = a.Note
                })
            );

            ItemsView = new System.Windows.Data.ListCollectionView(Accounts);
            ItemsView.Filter = FilterAccounts;

            Folders = new ObservableCollection<string>();
            Folders.Add("All");
            var distinctFolders = Accounts.Select(a => a.Folder).Where(f => !string.IsNullOrEmpty(f)).Distinct();
            foreach (var f in distinctFolders) Folders.Add(f);
            
            SelectedFolder = "All";

            SelectAllCommand = new ViewModels.RelayCommand(_ =>
            {
                var random = new System.Random();
                var randomizedList = ItemsView.Cast<FacebookAccount>().OrderBy(x => random.Next()).ToList();
                SelectedAccountsResult = new ObservableCollection<FacebookAccount>(randomizedList);
                DialogResult = true;
                Close();
            });

            DataContext = this;
        }

        private bool FilterAccounts(object obj)
        {
            if (obj is FacebookAccount acc)
            {
                if (SelectedFolder != "All" && acc.Folder != SelectedFolder) return false;
                
                if (!string.IsNullOrEmpty(SearchUid))
                {
                    var searchLines = SearchUid.Split(new[] { '\r', '\n', ',', ';' }, System.StringSplitOptions.RemoveEmptyEntries)
                                               .Select(l => l.Trim())
                                               .Where(l => !string.IsNullOrEmpty(l))
                                               .ToList();
                    if (searchLines.Count > 0)
                    {
                        bool match = false;
                        foreach (var line in searchLines)
                        {
                            if (acc.Uid?.Contains(line) ?? false)
                            {
                                match = true;
                                break;
                            }
                        }
                        if (!match) return false;
                    }
                }
                
                return true;
            }
            return false;
        }

        private void Confirm_Click(object sender, RoutedEventArgs e)
        {
            var grid = this.FindName("accountGrid") as System.Windows.Controls.DataGrid;
            if (grid != null && grid.SelectedItems.Count > 0)
            {
                SelectedAccountsResult = new ObservableCollection<FacebookAccount>(grid.SelectedItems.Cast<FacebookAccount>());
            }
            else
            {
                SelectedAccountsResult = new ObservableCollection<FacebookAccount>(Accounts.Where(a => a.IsSelected));
            }
            DialogResult = true;
            Close();
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
