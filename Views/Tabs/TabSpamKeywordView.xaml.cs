using System.Windows.Controls;
using FPlusClone.ViewModels;

namespace FPlusClone.Views.Tabs
{
    public partial class TabSpamKeywordView : UserControl 
    { 
        public TabSpamKeywordView() 
        { 
            InitializeComponent(); 
            DataContext = new TabSpamKeywordViewModel();
        } 
    }
}
