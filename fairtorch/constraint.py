import torch
from torch import nn
from torch.nn import functional as F


class L2PenaltyConstraintLoss(nn.Module):

    def __init__(self):
        super(L2PenaltyConstraintLoss, self).__init__()

    def forward(self, x):
        # x is size (c)
        # dim_constraint ->  1
        gap_constraint = F.relu(x)  # c -> a
        return torch.norm(gap_constraint, p=2)


class L1ExactPenaltyConstraintLoss(nn.Module):
    def __init__(self):
        super(L1ExactPenaltyConstraintLoss, self).__init__()

    def forward(self, x):
        # x is size (c)
        # dim_constraint ->  1
        gap_constraint = F.relu(x)  # c -> a
        return torch.norm(gap_constraint, p=1)


class L1ExactPenaltyConstraintLoss(nn.Module):
    def __init__(self):
        super(L1ExactPenaltyConstraintLoss, self).__init__()

    def forward(self, x):
        # x is size (c)
        # dim_constraint ->  1
        gap_constraint = F.relu(x)  # c -> a
        return torch.norm(gap_constraint, p=1)


class _BarrierConstraintLoss(nn.Module):
    def __init__(self):
        super(BarrierConstraintLoss, self).__init__()

    def forward(self, x):
        # x is size (c)
        # dim_constraint ->  1
        return -1 * torch.sum(torch.log(-1*x))


class ConstraintLoss(nn.Module):
    def __init__(self, n_class=2, alpha=1, penalty="exact_penalty", device="cpu"):
        """[summary]

        Args:
            n_class (int, optional): [description]. Defaults to 2.
            alpha (int, optional): [description]. Defaults to 1.
            penalty (str, optional): [description]. Defaults to "exact_penalty".
            device (str, optional): [description]. Defaults to "cpu".
        """        
        super(ConstraintLoss, self).__init__()
        if isinstance(device, torch.device):
            self.device = device
        else:
            self.device = torch.device(device)
        self.alpha = alpha
        self.n_class = n_class
        self.n_constraints = 2
        self.dim_condition = self.n_class + 1
        self.M = torch.zeros((self.n_constraints, self.dim_condition))
        self.c = torch.zeros(self.n_constraints)
        if penalty == "penalty":
            self.penalty_const = L2PenaltyConstraintLoss()
        elif penalty == "exact_penalty":
            self.penalty_const = L1ExactPenaltyConstraintLoss()
        else:
            self.penalty_const = L2PenaltyConstraintLoss()

    def mu_f(self, X=None, y=None, sensitive=None):
        """[summary]

        Args:
            X ([type], optional): [description]. Defaults to None.
            y ([type], optional): [description]. Defaults to None.
            sensitive ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """        
        return torch.zeros(self.n_constraints)

    def forward(self, X, out, sensitive, y=None):
        """[summary]

        Args:
            X ([type]): [description]
            out ([type]): [description]
            sensitive ([type]): [description]
            y ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """        
        sensitive = sensitive.view(out.shape)
        if isinstance(y, torch.Tensor):
            y = y.view(out.shape)
        out = torch.sigmoid(out)
        mu = self.mu_f(X=X, out=out, sensitive=sensitive, y=y)
        gap = torch.mv(self.M.to(self.device), mu.to(
            self.device)) - self.c.to(self.device)
        return self.penalty_const.forward(gap)


class DemographicParityLoss(ConstraintLoss):
    def __init__(self, sensitive_classes=[0, 1], alpha=1, penalty="penalty"):
        """loss of demograpfhic parity

        Args:
            sensitive_classes (list, optional): list of unique values of sensitive attribute. Defaults to [0, 1].
            alpha (int, optional): [description]. Defaults to 1.
            p_norm (int, optional): [description]. Defaults to 2.
        """
        self.sensitive_classes = sensitive_classes
        self.n_class = len(sensitive_classes)
        super(DemographicParityLoss, self).__init__(
            n_class=self.n_class, alpha=alpha, penalty=penalty
        )
        self.n_constraints = 2 * self.n_class
        self.dim_condition = self.n_class + 1
        self.M = torch.zeros((self.n_constraints, self.dim_condition))
        for i in range(self.n_constraints):
            j = i % 2
            if j == 0:
                self.M[i, j] = 1.0
                self.M[i, -1] = -1.0
            else:
                self.M[i, j - 1] = -1.0
                self.M[i, -1] = 1.0
        self.c = torch.zeros(self.n_constraints)

    def mu_f(self, X, out, sensitive, y=None):
        expected_values_list = []
        for v in self.sensitive_classes:
            idx_true = sensitive == v  # torch.bool
            expected_values_list.append(out[idx_true].mean())
        expected_values_list.append(out.mean())
        return torch.stack(expected_values_list)

    def forward(self, X, out, sensitive, y=None):
        return super(DemographicParityLoss, self).forward(X, out, sensitive)


class EqualiedOddsLoss(ConstraintLoss):
    def __init__(self, sensitive_classes=[0, 1], alpha=1, penalty="penalty"):
        """loss of demograpfhic parity

        Args:
            sensitive_classes (list, optional): list of unique values of sensitive attribute. Defaults to [0, 1].
            alpha (int, optional): [description]. Defaults to 1.
            p_norm (int, optional): [description]. Defaults to 2.
        """
        self.sensitive_classes = sensitive_classes
        self.y_classes = [0, 1]
        self.n_class = len(sensitive_classes)
        self.n_y_class = len(self.y_classes)
        super(EqualiedOddsLoss, self).__init__(
            n_class=self.n_class, alpha=alpha, penalty=penalty)
        # K:  number of constraint : (|A| x |Y| x {+, -})
        self.n_constraints = self.n_class * self.n_y_class * 2
        # J : dim of conditions  : ((|A|+1) x |Y|)
        self.dim_condition = self.n_y_class * (self.n_class + 1)
        self.M = torch.zeros((self.n_constraints, self.dim_condition))
        # make M (K * J): (|A| x |Y| x {+, -})  *   (|A|+1) x |Y|) )
        self.c = torch.zeros(self.n_constraints)
        element_K_A = self.sensitive_classes + [None]
        for i_a, a_0 in enumerate(self.sensitive_classes):
            for i_y, y_0 in enumerate(self.y_classes):
                for i_s, s in enumerate([-1, 1]):
                    for j_y, y_1 in enumerate(self.y_classes):
                        for j_a, a_1 in enumerate(element_K_A):
                            i = i_a * (2 * self.n_y_class) + i_y * 2 + i_s
                            j = j_y + self.n_y_class * j_a
                            self.M[i, j] = self.__element_M(
                                a_0, a_1, y_1, y_1, s)

    def __element_M(self, a0, a1, y0, y1, s):
        if a0 is None or a1 is None:
            x = y0 == y1
            return -1 * s * x
        else:
            x = (a0 == a1) & (y0 == y1)
            return s * float(x)

    def mu_f(self, X, out, sensitive, y):
        expected_values_list = []
        for u in self.sensitive_classes:
            for v in self.y_classes:
                idx_true = (y == v) * (sensitive == u)  # torch.bool
                expected_values_list.append(out[idx_true].mean())
        # sensitive is star
        for v in self.y_classes:
            idx_true = y == v
            expected_values_list.append(out[idx_true].mean())
        return torch.stack(expected_values_list)

    def forward(self, X, out, sensitive, y):
        return super(EqualiedOddsLoss, self).forward(X, out, sensitive, y=y)
