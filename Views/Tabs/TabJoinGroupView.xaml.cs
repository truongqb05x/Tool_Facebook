using System.Windows;
using System.Windows.Controls;
using FPlusClone.ViewModels;

namespace FPlusClone.Views.Tabs
{
    public partial class TabJoinGroupView : UserControl
    {
        public TabJoinGroupView()
        {
            InitializeComponent();
        }

        private void BtnStop_Click(object sender, RoutedEventArgs e)
        {
            if (MessageBox.Show("Bạn có chắc chắn muốn dừng tiến trình?", "Xác nhận", MessageBoxButton.YesNo, MessageBoxImage.Question) == MessageBoxResult.Yes)
            {
                if (DataContext is TabJoinGroupViewModel vm && vm.StopTaskCommand.CanExecute(null))
                {
                    vm.StopTaskCommand.Execute(null);
                    MessageBox.Show("Đã dừng tiến trình thành công!", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
        }
    }
}
